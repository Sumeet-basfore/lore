# Research Report 04: Enterprise DLP & Security Guardrails

**Document ID:** LORE-RES-004  
**Subject:** Data Loss Prevention (DLP), Secret Scrubbing, Shannon Entropy Detection, Intellectual Property Masking, and Enterprise Compliance  
**Date:** 2026-11-20  
**Author:** Antigravity Research Engine  

---

## 1. Executive Summary

In enterprise environments, engineering organizations enforce strict code confidentiality. The single greatest barrier preventing technical companies from adopting automated social content generators is the **fear of accidental intellectual property (IP) leakage or credential exposure**.

A single leaked API key, internal database connection string, customer domain, or proprietary algorithm diff in a public LinkedIn post or tweet can result in security breaches, regulatory penalties (GDPR/SOC2/HIPAA), and severe reputational damage.

This research establishes a multi-layer **Enterprise Data Loss Prevention (DLP)** framework specifically engineered for code-to-social pipelines, ensuring Lore meets the strict compliance standards required by CTOs, CISOs, and enterprise security review boards.

---

## 2. Threat Modeling: Code-to-Social Attack Vectors

```
+───────────────────────────────────────────────────────────────────────────────────+
|                           DATA EXFILTRATION THREAT VECTORS                        |
+──────────────────────────┬─────────────────────────────┬──────────────────────────+
| High Probability / Fatal | Medium Probability / Risky  | High Impact / Strategic  |
| - Hardcoded API keys     | - Internal staging domains  | - Proprietary math/algo  |
| - Database connection URI| - Customer/client identifiers| - Unreleased product     |
| - Private JWT secrets    | - Private IP addresses (RFC)|   feature codenames      |
+──────────────────────────┴─────────────────────────────┴──────────────────────────+
```

### 2.1 Threat Categories

1. **Credential & Secret Exposure (Catastrophic):**
   * AWS Access Keys (`AKIA...`), OpenAI API keys (`sk-...`), GitHub PATs (`ghp_...`), private SSH/RSA keys, Slack/Discord webhook URLs.
   * *Risk:* Instant server compromise, unauthorized cloud compute draining, data exfiltration.

2. **Network & Infrastructure Disclosure (Severe):**
   * Internal hostnames (`staging-db.internal.corp`), private IP addresses (`10.x.x.x`, `192.168.x.x`, `172.16.x.x`), Kubernetes cluster ingress definitions, VPC IDs.
   * *Risk:* Reconnaissance enablement for external threat actors.

3. **PII and Customer Identity Exposure (Compliance Violation):**
   * Customer tenant IDs, client emails found in test fixtures or migration seed scripts, real names in commit metadata.
   * *Risk:* GDPR/CCPA violations, breach of customer Non-Disclosure Agreements (NDAs).

4. **Proprietary Intellectual Property Leaks (Commercial Damage):**
   * Core proprietary algorithms (e.g. trading strategies, unique ML model architectures, patent-pending logic) inadvertently included in raw diff snippets.
   * *Risk:* Loss of trade secrets and competitive advantage.

---

## 3. Multi-Layer DLP Architecture for Lore

To achieve enterprise-grade security, Lore implements a **Defense-in-Depth** model consisting of four sequential validation gates:

```
[ Git Commits / Project Diffs ]
               │
               ▼
┌─────────────────────────────────────────┐
│ GATE 1: Path & File Blacklist           │  Excludes .env, secrets, *.pem, certs
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ GATE 2: Secret Signature Matching       │  Regex scanning (Gitleaks/TruffleHog rules)
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ GATE 3: Shannon Entropy Analysis        │  Catches high-entropy random strings/hashes
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ GATE 4: Proprietary Entity Masking      │  User-defined codenames, domains, salts
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ GATE 5: Local-First Scrubbing Boundary  │  Zero unscrubbed tokens leave the machine!
└──────────────┬──────────────────────────┘
               │
               ▼
[ Sanitized Evidence Ledger -> LLM Generation ]
```

---

## 4. Technical Implementation of DLP Layers

### 4.1 Gate 1: Strict Path & Pattern Filtering
The scanner rejects any file matching sensitive extensions or known secret locations before extracting diffs:
- Files: `.env`, `.env.*`, `*credentials*`, `*secret*`, `*token*`, `id_rsa`, `id_ed25519`, `*.pem`, `*.p12`, `*.key`, `*.keystore`.
- Directories: `.git`, `credentials/`, `certs/`, `build/`, `dist/`, `node_modules/`, `venv/`.

### 4.2 Gate 2: High-Precision Secret Regex Engine
Lore adopts the proven pattern signatures from **Gitleaks** and **TruffleHog**:

| Secret Type | Regex Pattern Specification | Action on Match |
|---|---|---|
| **AWS Access Key** | `(?i)\b(AKIA[0-9A-Z]{16})\b` | HARD BLOCK: Drop atom immediately |
| **OpenAI / Claude Key** | `\b(sk-[a-zA-Z0-9_-]{32,64})\b` | HARD BLOCK: Drop atom immediately |
| **GitHub Token** | `\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b` | HARD BLOCK: Drop atom immediately |
| **Slack Webhook** | `https:\/\/hooks\.slack\.com\/services\/T[0-9A-Z_]+\/B[0-9A-Z_]+\/[0-9A-Za-z_]+` | HARD BLOCK: Drop atom immediately |
| **Private SSH Key Header**| `-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----` | HARD BLOCK: Drop atom immediately |
| **Database Connection URI**| `[a-zA-Z]+:\/\/[a-zA-Z0-9_]+:[^@\s]+@[a-zA-Z0-9.-]+:[0-9]+\/[a-zA-Z0-9_]+` | Redact URI parameters |

### 4.3 Gate 3: Shannon Entropy Scoring
Hardcoded passwords and cryptographic secrets frequently escape static regex patterns. Lore employs Shannon Entropy detection:

$$H(X) = -\sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$

* **Entropy Thresholds:**
  * Base64 / Hex Strings > 16 chars with $H(X) > 4.5$: Flagged as potential secret.
  * Standard alphanumeric text: $H(X)$ typically ranges between $2.5$ and $3.8$.
* **Handling:** Any token exceeding the threshold that is not part of a standard import path or git SHA is automatically redacted (`[REDACTED_SECRET_HIGH_ENTROPY]`).

### 4.4 Gate 4: Named Entity & Proprietary Domain Masking
Enterprises can specify custom masking rules in `.lorerc.yaml`:
```yaml
security:
  dlp_enabled: true
  entropy_threshold: 4.5
  custom_masks:
    - pattern: "corp\\.internal\\.domain"
      replacement: "[INTERNAL_DOMAIN]"
    - pattern: "ProjectTitan"
      replacement: "Project [CODENAME]"
    - pattern: "\\b[0-9]{3}-[0-9]{2}-[0-9]{4}\\b"
      replacement: "[SSN_REDACTED]"
```

---

## 5. Local-First Boundary & Compliance Guarantee

The fundamental architectural principle that makes Lore enterprise-viable is the **Local Execution Boundary**:

1. **Zero Raw Code Transmission:** The Git scanner, AST parser, and DLP filters execute entirely on the developer's local machine or within their self-hosted CI/CD runner.
2. **Pre-LLM Sanitization:** Diffs are sanitized *before* reaching any LLM prompt. If a cloud LLM (OpenAI, Anthropic) is used, it only receives scrubbed, sanitized summaries.
3. **Local LLM Isolation:** If an enterprise strictly forbids cloud AI, Lore runs with local Ollama (`gemma4`, `llama3`, `qwen3`), ensuring that **zero bytes of text or metadata leave the internal corporate network**.
4. **Audit Provenance Ledger:** Every draft generated includes an immutable SHA256 signature and a record of every filter rule evaluated, providing complete auditability for SOC2 and ISO 27001 certification.

---

## 6. Strategic Takeaway for Enterprise Monetization

Security is not merely a feature; it is the **primary wedge for enterprise pricing**. While solo developers value time-savings, enterprise CTOs buy **risk mitigation**. 

By offering a verifiable, Gitleaks-backed DLP shield, Lore can comfortably charge **$299–$499/month per organization** for its Enterprise tier, where generic tools like Buffer or Taplio are instantly rejected during vendor security reviews.
