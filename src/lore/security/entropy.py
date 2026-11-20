"""Alphabet-specific Shannon entropy calculator and git SHA verification."""

import math
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def calculate_shannon_entropy(token: str) -> float:
    """Calculates Shannon entropy in bits per character."""
    if not token:
        return 0.0
    length = len(token)
    counts = Counter(token)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 3)


def is_base16_hex(token: str) -> bool:
    """Returns True if the token consists exclusively of hexadecimal characters."""
    return bool(re.fullmatch(r"^[0-9a-fA-F]+$", token))


def verify_git_sha(sha: str, repo_path: Optional[Path] = None, known_shas: Optional[Set[str]] = None) -> bool:
    """Verifies whether a 40-char (SHA-1) or 64-char (SHA-256) hex string is a commit in the git repository.
    Does NOT blindly trust hexadecimal strings.
    """
    if (len(sha) not in (40, 64)) or not is_base16_hex(sha):
        return False

    if known_shas and sha.lower() in {s.lower() for s in known_shas}:
        return True

    target_repo = repo_path or Path.cwd()
    if target_repo and (target_repo / ".git").exists():
        try:
            res = subprocess.run(
                ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                cwd=str(target_repo),
                capture_output=True,
                text=True,
            )
            return res.returncode == 0
        except Exception:
            return False

    return False


def scan_text_entropy(
    text: str,
    repo_path: Optional[Path] = None,
    known_shas: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """Scans text for high-entropy secrets using alphabet-specific thresholds.
    - Pure Hex (Base16): len >= 24, entropy >= 3.75
    - Base64 / ASCII: len >= 24, entropy >= 4.8
    - Sensitive variable assignment context: len >= 10, entropy >= 3.2
    - Data URIs whitelisted.
    - 40-char hex strings whitelisted ONLY if verified as local Git commits.
    """
    candidates: List[Dict[str, Any]] = []

    for line_idx, raw_line in enumerate(text.splitlines(), start=1):
        # Chunk lines longer than 2,048 chars to avoid regex timeouts while preventing blind spots
        chunks = [raw_line] if len(raw_line) <= 2048 else [raw_line[i:i + 1024] for i in range(0, len(raw_line), 896)]
        for chunk in chunks:
            # Whitelist data: URIs
            if "data:image/" in chunk or "data:application/" in chunk or "data:font/" in chunk:
                continue

            # Check for assignment context
            is_sensitive_assignment = bool(
                re.search(
                    r"(?:password|api[_-]?key|secret|token|credential|auth)[^\w=]*=[^\w]*['\"]?([^'\"\s;]+)",
                    chunk,
                    re.IGNORECASE,
                )
            )

            tokens = re.findall(r"[A-Za-z0-9+/=_\-]{10,}", chunk)
            for token in tokens:
                clean_token = token.rstrip("=;\"',")
                tok_len = len(clean_token)
                if tok_len < 10:
                    continue

                entropy = calculate_shannon_entropy(clean_token)
                is_hex = is_base16_hex(clean_token)

                # Check 40-char (SHA-1) or 64-char (SHA-256) hex commit verification
                if tok_len in (40, 64) and is_hex:
                    if verify_git_sha(clean_token, repo_path=repo_path, known_shas=known_shas):
                        continue  # Verified commit SHA, whitelist!

                # Evaluate thresholds
                is_high_entropy = False
                rule_matched = ""

                if is_sensitive_assignment and tok_len >= 10 and entropy >= 3.2:
                    is_high_entropy = True
                    rule_matched = f"sensitive_assignment_context (len={tok_len}, entropy={entropy})"
                elif is_hex and tok_len >= 24 and entropy >= 3.75:
                    is_high_entropy = True
                    rule_matched = f"base16_hex_secret (len={tok_len}, entropy={entropy})"
                elif not is_hex and tok_len >= 24 and entropy >= 4.8:
                    is_high_entropy = True
                    rule_matched = f"base64_high_entropy (len={tok_len}, entropy={entropy})"

                if is_high_entropy:
                    candidates.append(
                        {
                            "token": clean_token,
                            "line": line_idx,
                            "length": tok_len,
                            "entropy": entropy,
                            "rule": rule_matched,
                        }
                    )

    return candidates
