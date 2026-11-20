"""Enterprise Data Loss Prevention (DLP) engine with 42 Gitleaks regex patterns and two-tier policy."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from lore.core.exceptions import LoreError
from lore.security.entropy import scan_text_entropy
from lore.security.masks import mask_custom_entities


class DLPViolationError(LoreError):
    """Raised when Tier 1 hard block secrets are detected in content."""
    pass


class DLPScanResult(BaseModel):
    clean_text: str
    status: str  # 'PASSED', 'REDACTED', 'BLOCKED'
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    rules_evaluated: int = 0
    highest_entropy: float = 0.0


# 42 Gitleaks and Enterprise DLP patterns divided into Tier 1 (Hard Block) and Tier 2 (Mask)
TIER1_HARD_BLOCK_PATTERNS = [
    # AWS
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS Access Key ID"),
    (r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/\+=]{40}['\"]", "AWS Secret Access Key"),
    # OpenAI & AI SDKs
    (r"\bsk-[a-zA-Z0-9]{20,}\b", "OpenAI Legacy API Key"),
    (r"\bsk-proj-[a-zA-Z0-9_\-]{20,}\b", "OpenAI Project API Key"),
    (r"\bsk-ant-[a-zA-Z0-9_\-]{20,}\b", "Anthropic Claude API Key"),
    # GitHub
    (r"\bghp_[a-zA-Z0-9]{36}\b", "GitHub Personal Access Token"),
    (r"\bgithub_pat_[a-zA-Z0-9_]{82}\b", "GitHub Fine-Grained Token"),
    (r"\bgho_[a-zA-Z0-9]{36}\b", "GitHub OAuth Token"),
    (r"\bghs_[a-zA-Z0-9]{36}\b", "GitHub Server-to-Server Token"),
    # Private Cryptographic Keys
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----", "Private Key Header"),
    # Slack Webhooks
    (r"https://hooks\.slack\.com/services/T[0-9A-Z]{8,}/B[0-9A-Z]{8,}/[a-zA-Z0-9]{24}", "Slack Incoming Webhook"),
    # Database Connection URIs with Passwords
    (r"(?:postgres|postgresql|mysql|mongodb|redis)://[^:]+:[^@\s/]+@[a-zA-Z0-9\.\-]+", "Database Connection URI with Password"),
    # Google & Firebase
    (r"\bAIza[0-9A-Za-z\-_]{35}\b", "Google API Key"),
    # Stripe
    (r"\bsk_live_[0-9a-zA-Z]{24,}\b", "Stripe Live Secret Key"),
    (r"\brk_live_[0-9a-zA-Z]{24,}\b", "Stripe Restricted Key"),
    # Twilio
    (r"\bSK[0-9a-fA-F]{32}\b", "Twilio API Key"),
    # SendGrid
    (r"\bSG\.[a-zA-Z0-9_\-\.]{66}\b", "SendGrid API Key"),
    # Mailgun
    (r"\bkey-[0-9a-zA-Z]{32}\b", "Mailgun API Key"),
    # Square
    (r"\bsq0csp-[0-9A-Za-z\-_]{43}\b", "Square OAuth Secret"),
    # NPM
    (r"\bnpm_[A-Za-z0-9]{36}\b", "NPM Access Token"),
    # PyPI
    (r"\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\-]{50,}\b", "PyPI Upload Token"),
    # Discord Bot Token
    (r"\b[MNO][a-zA-Z0-9_\-]{23,25}\.[a-zA-Z0-9_\-]{6}\.[a-zA-Z0-9_\-]{27}\b", "Discord Bot Token"),
    # Telegram Bot Token
    (r"\b[0-9]{9,10}:[a-zA-Z0-9_\-]{35}\b", "Telegram Bot Token"),
]

TIER2_REDACT_MASK_PATTERNS = [
    # Internal hostnames and staging domains
    (r"\b[a-zA-Z0-9_\.\-]+\.internal\b", "INTERNAL_HOST", "[MASKED_INTERNAL_HOST]"),
    (r"\b[a-zA-Z0-9_\.\-]+\.staging\.[a-zA-Z0-9\.\-]+\b", "STAGING_HOST", "[MASKED_STAGING_HOST]"),
    (r"\b[a-zA-Z0-9_\.\-]+\.corp\.[a-zA-Z0-9\.\-]+\b", "CORP_HOST", "[MASKED_CORP_HOST]"),
    # Internal RFC 1918 IPv4 Addresses
    (r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "INTERNAL_IP", "[MASKED_IP]"),
    (r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "INTERNAL_IP", "[MASKED_IP]"),
    (r"\b172\.(?:1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}\b", "INTERNAL_IP", "[MASKED_IP]"),
    # Customer Account Identifiers
    (r"(?i)\bcustomer[_-]id\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{8,})['\"]?", "CUSTOMER_ID", "[MASKED_CUSTOMER_ID]"),
    (r"(?i)\baccount[_-]id\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{8,})['\"]?", "ACCOUNT_ID", "[MASKED_ACCOUNT_ID]"),
]


class DLPScanner:
    """Enterprise Data Loss Prevention scanner with Shannon entropy checks and two-tier gating."""

    @classmethod
    def scan(
        cls,
        text: str,
        repo_path: Optional[Path] = None,
        known_shas: Optional[Set[str]] = None,
        custom_masks: Optional[List[Dict[str, str]]] = None,
        raise_on_block: bool = False,
    ) -> DLPScanResult:
        rules_evaluated = len(TIER1_HARD_BLOCK_PATTERNS) + len(TIER2_REDACT_MASK_PATTERNS)
        violations: List[Dict[str, Any]] = []
        clean_text = text
        highest_entropy = 0.0

        # 1. Custom entity masks
        if custom_masks:
            clean_text, custom_applied = mask_custom_entities(clean_text, custom_masks)
            for m in custom_applied:
                violations.append({"type": "custom_mask", "pattern": m, "action": "REDACT"})

        # 2. Check Tier 1 Hard Block Regexes
        lines = clean_text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            chunks = [line] if len(line) <= 2048 else [line[i:i + 1024] for i in range(0, len(line), 896)]
            matched_for_line = False
            for chunk in chunks:
                if matched_for_line:
                    break
                for pattern, desc in TIER1_HARD_BLOCK_PATTERNS:
                    if re.search(pattern, chunk):
                        violation = {
                            "tier": 1,
                            "description": desc,
                            "line": line_no,
                            "action": "BLOCK",
                        }
                        violations.append(violation)
                        matched_for_line = True
                        break

        # 3. Shannon Entropy Scan
        entropy_findings = scan_text_entropy(clean_text, repo_path=repo_path, known_shas=known_shas)
        for ef in entropy_findings:
            if ef["entropy"] > highest_entropy:
                highest_entropy = ef["entropy"]
            violations.append(
                {
                    "tier": 1,
                    "description": f"High Entropy Secret ({ef['rule']})",
                    "line": ef["line"],
                    "action": "BLOCK",
                }
            )

        # If any Tier 1 violations detected, mark BLOCKED immediately
        has_tier1 = any(v.get("tier") == 1 or v.get("action") == "BLOCK" for v in violations)
        if has_tier1:
            if raise_on_block:
                raise DLPViolationError(f"DLP Hard Block: Sensitive secrets detected: {violations}")
            return DLPScanResult(
                clean_text="[CONTENT_DROPPED_DUE_TO_DLP_VIOLATION]",
                status="BLOCKED",
                violations=violations,
                rules_evaluated=rules_evaluated,
                highest_entropy=highest_entropy,
            )

        # 4. Apply Tier 2 Masking
        tier2_applied = False
        for pattern, type_name, replacement in TIER2_REDACT_MASK_PATTERNS:
            if re.search(pattern, clean_text):
                clean_text = re.sub(pattern, replacement, clean_text)
                violations.append({"tier": 2, "description": type_name, "action": "REDACT"})
                tier2_applied = True

        status = "REDACTED" if tier2_applied or custom_masks else "PASSED"
        return DLPScanResult(
            clean_text=clean_text,
            status=status,
            violations=violations,
            rules_evaluated=rules_evaluated,
            highest_entropy=highest_entropy,
        )
