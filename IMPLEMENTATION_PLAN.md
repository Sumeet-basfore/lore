# LORE v2.0 — Master Technical Implementation Plan

**Document ID:** LORE-IMP-001  
**Target Product:** Lore (`lore-cli`, `lore-mcp`, `lore-cloud`)  
**Specification Reference:** `PRD.md`, `LORE-RES-001` through `LORE-RES-007`  
**Peer Review Approvals:**  
- Systems & Security Architecture Reviewer (`99f1ab86`)  
- Developer Experience & Humanization Reviewer (`d9d7da9f`)  
- QA & Release Engineering Reviewer (`d65f8baa`)  
**Status:** **AUDITED, HARDENED & IMPLEMENTATION READY**  

---

## 1. System Architecture Overview

Lore v2.0 evolves from a local Git CLI into a **commercial-grade, developer-first content manager**. The implementation maintains strict local execution boundaries while enabling high-converting visual diff cards, enterprise-grade DLP secret scrubbing, a 2-stage hybrid anti-slop humanizer with a Hacker News critic gate, asynchronous approval channels, and an official Model Context Protocol (MCP) server.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   LORE v2.0 CODEBASE TOPOLOGY                                   │
├───────────────────────────────────┬─────────────────────────────────┬────────────────────────────┤
│ 1. INGESTION & EXTRACTION         │ 2. SECURITY & DLP               │ 3. INTELLIGENCE & SLOP     │
│ - git_scanner.py (include_wip=F)  │ - dlp_scanner.py (Gitleaks)     │ - angle_finder.py (7 angles│
│ - project_walker.py               │ - entropy.py (Base16 & Base64)  │ - humanizer.py (2-stage)   │
│ - ast_inspector.py (AST Diffs)    │ - masks.py (Custom entity masks)│ - critic.py (HN Critic Pass│
│ - atom_extractor.py (Hero file)   │ - audit.py (Immutable ledger)   │ - voice.py (Local RAG)     │
├───────────────────────────────────┼─────────────────────────────────┼────────────────────────────┤
│ 4. VISUAL CODE CARDS              │ 5. APPROVAL GATEWAYS            │ 6. PUBLISHING & PLATFORMS  │
│ - card_generator.py (resvg/freeze)│ - local_web.py (Port 4748 WebUI)│ - publisher.py (Router)    │
│ - layout_engine.py (Base64 font)  │ - slack_gateway.py (httpx Block)│ - linkedin.py (Restli v2)  │
│ - themes.py (Catppuccin, Tokyo)   │ - discord_gateway.py (httpx)    │ - bluesky.py (ATProto)     │
│ - ast_diff_truncator.py (No-wrap) │ - telegram_gateway.py (httpx)   │ - twitter_bridge.py (Intent│
├───────────────────────────────────┴─────────────────────────────────┴────────────────────────────┤
│ 7. INTEGRATIONS & EXTENSIONS: mcp_server.py (FastMCP / stdio JSON-RPC for Cursor / Claude Code) │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Module Blueprint

```
projects/lore/src/lore/
├── __init__.py
├── cli.py                     # Click CLI commands (scan, generate, review, approve, export, etc.)
├── config.py                  # Pydantic v2 Settings (.lorerc.yaml + ENV overrides)
├── core/
│   ├── database.py            # SQLite synchronous connection, PRAGMA user_version migration engine
│   ├── exceptions.py          # Domain exception hierarchy (DLPViolationError, TokenExpiredError, etc.)
│   └── models.py              # Canonical Pydantic schemas with backward-compatible defaults
├── scanner/
│   ├── git_scanner.py         # Git log, diff-tree, branch analysis, worktree support
│   ├── project_walker.py      # Manifest & documentation context extractor
│   ├── filters.py             # File path blacklist & ignore rules (contract preserved)
│   └── ast_inspector.py       # [NEW] AST structural diff parser for messy 'wip' commits & dirty trees
├── extraction/
│   ├── atom_extractor.py      # Commit clustering (4h window), Hero File selection, atom classification
│   └── evidence.py            # Evidence Ledger with cryptographic SHA verification
├── security/                  # [NEW] Enterprise DLP & Guardrails
│   ├── __init__.py
│   ├── dlp_scanner.py         # 42 Gitleaks regex patterns + Two-tier policy (Block vs Mask)
│   ├── entropy.py             # Shannon entropy (Base16 >= 3.75, Base64 >= 4.8) + Git SHA verification
│   ├── masks.py               # AST loop masking & custom regex redactions
│   └── audit.py               # Compliance audit trail logger (target_type: commit/atom/draft)
├── intelligence/
│   ├── angle_finder.py        # 7 developer angle classifiers (including "What We Deleted" & "TIL")
│   └── calendar.py            # Optimal scheduling & posting cadences
├── generation/
│   ├── router.py              # LLM router (Ollama, Anthropic, Gemini, OpenAI, mock)
│   ├── prompts/               # Jinja2 templates (X, thread, LinkedIn, blog, release)
│   ├── humanizer.py           # 2-stage hybrid humanizer (instant regex scrub + LLM refinement)
│   ├── critic.py              # [NEW] "Hacker News Critic Pass" evaluation gate
│   └── voice.py               # Personal style calibration & local writing sample RAG
├── visual/                    # [NEW] Headless Code-to-Image Diff Generator
│   ├── __init__.py
│   ├── assets/fonts/          # Bundled JetBrainsMono-Regular.ttf (inlined in SVG)
│   ├── card_generator.py      # Multi-tier rasterizer (freeze binary -> resvg-py -> raw SVG)
│   ├── layout_engine.py       # Mathematical character-width line calculator (16:9 and 1:1)
│   ├── ast_diff_truncator.py  # Hard wrap ban (max 84 cols / 14-20 lines) + semantic ellipsis
│   └── themes.py              # Tokyo Night, Catppuccin Mocha, One Dark (WCAG AA > 4.5:1)
├── approval/                  # [NEW] Asynchronous Approval Gateways
│   ├── __init__.py
│   ├── local_web.py           # ThreadingHTTPServer on 127.0.0.1:4748 + in-browser markdown editor
│   ├── slack_gateway.py       # Slack Block Kit dispatcher via httpx + modal edit support
│   ├── discord_gateway.py     # Discord component embed webhook dispatcher via httpx
│   └── telegram_gateway.py    # Telegram bot 1-tap approval listener via httpx + ForceReply edit
├── publishing/
│   ├── exporter.py            # Clipboard, JSON, and Markdown export
│   ├── social_router.py       # [NEW] Multi-platform dispatcher with exponential backoff
│   ├── linkedin.py            # [NEW] LinkedIn Restli v2 API + offline_access token lifecycle
│   ├── bluesky.py             # [NEW] AT Protocol repo creator with UTF-8 byte offset facets
│   ├── twitter_bridge.py      # [NEW] Twitter Web Intent + automated PNG clipboard copy
│   └── github_release.py      # [NEW] GitHub REST API release notes generator
└── mcp/                       # [NEW] Model Context Protocol Server
    ├── __init__.py
    └── server.py              # FastMCP / stdio JSON-RPC server for Cursor, Windsurf, Claude Code
```

---

## 3. Database Schema Migrations (SQLite)

### Schema Versioning via `PRAGMA user_version`
`src/lore/core/database.py` implements an idempotent, non-destructive migration engine that inspects existing columns via `PRAGMA table_info` before altering tables, preserving 100% of existing user data:

```sql
-- Migration 002: DLP & Visual Asset Support (Executed conditionally in Phase 0)

-- Idempotently alter drafts table
-- Checked via PRAGMA table_info(drafts):
-- card_image_path TEXT
-- dlp_status TEXT DEFAULT 'clean'
-- dlp_audit_json TEXT
-- scheduled_for TEXT
-- channel_target TEXT

-- DLP Compliance Audit Log Table (Flexible target auditing: commit, atom, or draft)
CREATE TABLE IF NOT EXISTS dlp_audit_logs (
    id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL, -- 'commit', 'atom', 'draft'
    target_id TEXT NOT NULL,
    draft_id TEXT, -- optional reference to drafts(id)
    scanned_at TEXT NOT NULL, -- ISO-8601 UTC
    rules_evaluated INTEGER NOT NULL,
    violations_detected INTEGER NOT NULL,
    masked_entities_json TEXT,
    highest_entropy_score REAL,
    status TEXT NOT NULL -- 'PASSED', 'REDACTED', 'BLOCKED'
);

-- Scheduled Social Publish Queue
CREATE TABLE IF NOT EXISTS publish_queue (
    id TEXT PRIMARY KEY,
    draft_id TEXT NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    scheduled_time TEXT NOT NULL, -- ISO-8601 UTC
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'publishing', 'success', 'failed'
    created_at TEXT NOT NULL -- ISO-8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_dlp_target ON dlp_audit_logs(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_publish_queue_status ON publish_queue(status, scheduled_time);

-- Update schema version
PRAGMA user_version = 2;
```

---

## 4. Phased Implementation Roadmap & Detailed Tasks

```
Phase 0: Database Migration Engine & Model Evolution (Prerequisite)
Phase 1: AST Structural Code Inspection & Dirty Commit Ingestion
Phase 2: Enterprise DLP & Shannon Entropy Engine
Phase 3: 5-Stage Anti-Slop Humanizer & Hacker News Critic Gate
Phase 4: Headless Code-to-Image Visual Diff Card Generator
Phase 5: Asynchronous Headless Approval Gateway & Web Dashboard
Phase 6: Multi-Platform Publishing Engine (LinkedIn, Bluesky, GitHub)
Phase 7: Model Context Protocol (MCP) Server for AI IDEs
```

---

### Phase 0: Database Migration Engine & Model Evolution

#### Objective
Ensure existing databases (`~/.lore/lore.db`) evolve to schema v2 idempotently without data loss, and update models with default values to preserve existing tests.

#### Tasks & Acceptance Criteria
* **Task 0.1: Update `src/lore/core/models.py`**
  * Update `Draft` with default values for all new fields:
    ```python
    card_image_path: Optional[str] = None
    dlp_status: str = "clean"
    dlp_audit_json: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[datetime] = None
    channel_target: Optional[str] = None
    ```
  * Add new data models: `DLPAuditLog`, `PublishQueueItem`, `ASTDiffReport`.
* **Task 0.2: Implement Idempotent Migration Runner in `src/lore/core/database.py`**
  * Check `PRAGMA user_version`. If $< 2$, execute `_migrate_v1_to_v2()`:
    - Inspect columns of `drafts` via `PRAGMA table_info(drafts)`. Add only missing columns.
    - Create `dlp_audit_logs` and `publish_queue` tables.
    - Set `PRAGMA user_version = 2`.
  * Add DAO methods: `log_dlp_audit()`, `enqueue_publish()`, `get_pending_publishes()`, `update_publish_status()`.
* **Verification Gate:**
  * Run `pytest tests/test_core.py`.
  * Verify all 4 existing database and model tests pass with zero regressions.

---

### Phase 1: AST Structural Code Inspection & Dirty Commit Ingestion

#### Objective
Eliminate the "Clean Commit Fallacy". Extract high-value content atoms even when commit messages are `wip`, `fix`, `asdf`, or when uncommitted changes exist in dirty trees, while preserving the existing noise filter contract.

#### Tasks & Acceptance Criteria
* **Task 1.1: Implement `src/lore/scanner/ast_inspector.py`**
  * Use Python standard library `ast` for Python source files.
  * Implement deterministic regex/token AST lexer fallbacks for TypeScript/JavaScript, Rust, and Go. (Tree-sitter treated as strictly optional).
  * Function `inspect_diff_changes(repo_path: Path, changed_files: List[str], diff_text: str) -> ASTDiffReport`:
    - Reads the full source file to build AST; maps diff line numbers (`+` lines) against AST node spans (`lineno` to `end_lineno`).
    - Identifies modified classes, exported functions, and schema migrations.
    - **Extracts inline comments and docstrings** added in diff hunks to capture developer intent.
    - **Extracts test assertions** (`assert`, `expect(...)`) from test files to isolate the bug reproduction narrative.
* **Task 1.2: Upgrade `src/lore/scanner/git_scanner.py` & `filters.py`**
  * Retain `is_noise_commit()` contract intact to preserve `test_filters` and `test_git_scanner`.
  * Update `GitScanner.scan_commits(self, since=None, until=None, include_wip: bool = False)`:
    - Default remains `include_wip=False` (preserves existing 2-commit count in `test_git_scanner`).
    - When `include_wip=True` (or `--include-wip`), commits matching WIP patterns are retained and flagged with `is_low_entropy=True`.
  * Support Git worktrees and submodules in `GitScanner.__init__` by checking `(self.repo_path / ".git").exists()`.
  * Handle empty git repositories (0 commits) gracefully without throwing exit code 128 crashes.
* **Task 1.3: Upgrade `src/lore/extraction/atom_extractor.py`**
  * **Branch Name Semantic Harvesting:** Capture active branch (`git rev-parse --abbrev-ref HEAD`). Parse slug (e.g. `fix/pg-pool-leak` -> "Fixing connection pool leak").
  * **Commit Cluster Aggregation:** Group consecutive commits on the same branch within a 4-hour window into a single unified atom.
  * **Hero File Selection:** Score files in multi-file diffs. Select the primary domain hero file for diff card rendering; filter out lockfiles (`poetry.lock`, `package-lock.json`).
  * If a commit has `is_low_entropy=True`, synthesize atom title from AST mutation + branch intent + test assertion.
* **Task 1.4: Support Uncommitted Staged/Unstaged Trees**
  * Add flag `lore scan --include-working-tree` to inspect `git diff HEAD`.
* **Verification Gate:**
  * Run `pytest tests/test_scanner.py tests/test_extraction.py`.
  * Add `tests/test_ast_inspector.py` testing AST diff inspection on Python and TypeScript fixtures. Verify 100% test pass.

---

### Phase 2: Enterprise DLP & Shannon Entropy Engine

#### Objective
Build a mathematically rigorous, multi-gate security shield that prevents sensitive credentials, internal staging URLs, or proprietary trade secret loop implementations from leaving the developer's workstation.

#### Tasks & Acceptance Criteria
* **Task 2.1: Implement `src/lore/security/entropy.py`**
  * Function `calculate_shannon_entropy(token: str) -> float`.
  * Implement **Alphabet-Specific Thresholds**:
    - Pure Hexadecimal (Base16): Length $\ge 24$, threshold $\ge 3.75$.
    - Base64 / ASCII: Length $\ge 24$, threshold $\ge 4.8$.
  * **Git SHA Whitelist Verification:** Do NOT blindly whitelist all 40-character hex strings. A 40-character hex string is ONLY whitelisted if it is verified against the local Git repository via `git cat-file -e <sha>^{commit}` or matches an existing commit in `EvidenceRecord.commits`. Any naked 40-character hex token assigned to a variable is treated as a candidate secret!
  * Whitelist `data:` URIs and base64 image headers to prevent false positives on embedded assets.
  * Implement assignment context detection: if a token appears in an assignment to a sensitive variable name (`password`, `api_key`, `token`, `secret`), run entropy and secret evaluation on tokens with length $\ge 10$ and entropy $\ge 3.2$.
* **Task 2.2: Implement `src/lore/security/dlp_scanner.py`**
  * Embed 42 Gitleaks regex patterns (AWS keys, OpenAI/Anthropic tokens, GitHub PATs, private SSH keys, Slack webhook URLs, database connection URIs).
  * Skip lines longer than 2,048 characters to eliminate ReDoS risks.
  * Implement **Two-Tier Enforcement Hierarchy**:
    - **Tier 1 (Hard Block):** Cloud API keys, private SSH keys, database URIs with passwords. Instantly aborts draft generation, drops the atom, and issues a warning. Zero bytes forwarded to any LLM.
    - **Tier 2 (Redact / Mask):** Internal hostnames, staging domains, customer IDs, proprietary algorithm loops. Substituted with `[MASKED_<TYPE>]` and allowed to proceed.
* **Task 2.3: Implement `src/lore/security/masks.py`**
  * Custom entity masking from `.lorerc.yaml` (`security.custom_masks`).
  * **AST Loop Masking:** Abstract deep algorithmic loop bodies into `// ... [proprietary implementation hidden]` to protect proprietary mathematical IP. (Operates on full source files mapped to diff line numbers).
* **Task 2.4: Implement Audit Logger in `src/lore/security/audit.py`**
  * Log every DLP scan to `dlp_audit_logs` table (`target_type: commit/atom/draft`).
* **Verification Gate:**
  * Add `tests/test_dlp.py`. Test against synthetic AWS keys (`AKIA...`), test OpenAI tokens (`sk-...`), and test high-entropy base64 secrets. Verify 100% detection rate and zero false positives on verified Git SHAs and UUIDs.

---

### Phase 3: 5-Stage Anti-Slop Humanizer & Hacker News Critic Gate

#### Objective
Ensure all generated content completely passes the "Hacker News & Tech Twitter Smell Test" by breaking formulaic AI essay structures, eliminating buzzwords, and injecting authentic engineering texture.

#### Tasks & Acceptance Criteria
* **Task 3.1: Expand Content Angles in `src/lore/intelligence/angle_finder.py`**
  * Implement 7 developer angles:
    1. `ARCHITECTURE_TRADEOFF`: Why we chose X over Y.
    2. `POST_MORTEM_BUG`: Subtle race condition / production issue.
    3. `BEFORE_AFTER_BENCHMARK`: Cutting memory / latency with real numbers.
    4. `FEATURE_DROP`: Shipping native capability in clean lines.
    5. `WHAT_WE_DELETED`: Code deletion, removing complex abstractions.
    6. `TIL_LANGUAGE_QUIRK`: Standard library nuances, compiler quirks.
    7. `PROTOTYPE_HACK`: Speed of iteration, building MVP in <100 lines.
* **Task 3.2: Implement 2-Stage Hybrid Humanizer in `src/lore/generation/humanizer.py`**
  * Maintain exact return signature:
    `Humanizer.humanize(text: str, config: Optional[LoreConfig] = None) -> Tuple[str, Dict[str, Any]]`
  * **Pass 1 (Grounded Generation):** Generate initial draft bound strictly to Evidence Ledger facts.
  * **Deterministic Scrubbing Pass (<1ms, zero LLM latency):**
    - Regex scrub 35+ forbidden marketing tokens (*delve, intricate, crucial, tapestry, leverage, game-changer, etc.*).
    - Regex strip formulaic closing questions (*"What do you think? 👇"*, *"Let me know below"*).
    - Regex strip chatbot greetings and preambles.
    - Measure sentence length standard deviation; fail if all sentences are uniform.
* **Task 3.3: Implement Structured HN Critic Gate in `src/lore/generation/critic.py`**
  * When `LORE_MOCK_LLM=1` or `force_mock=True`, evaluate deterministically without external API calls.
  * Invoke LLM with strict JSON schema:
    ```json
    {
      "fluff_detected": bool,
      "unsubstantiated_claims": [{"claim": str, "fix": str}],
      "sanitized_copy": str
    }
    ```
  * Critic prompt rules:
    1. Strike any performance/speed claims not backed by numbers in the Evidence Ledger.
    2. Ban single-sentence vertical paragraph spacing on non-LinkedIn platforms.
    3. Require understated, technical vocabulary.
  * Run final deterministic regex scrubber on sanitized copy to guarantee zero buzzword regressions.
* **Verification Gate:**
  * Run `pytest tests/test_humanizer.py tests/test_intelligence.py`.
  * Add `tests/test_critic.py`. Validate that drafts have zero banned tokens, zero formulaic closing questions, and include specific environment names.

---

### Phase 4: Headless Code-to-Image Visual Diff Card Generator

#### Objective
Produce stunning, high-contrast syntax-highlighted code diff cards (PNG/SVG) from git diffs with zero dependency on headless browsers.

#### Tasks & Acceptance Criteria
* **Task 4.1: Implement `src/lore/visual/ast_diff_truncator.py`**
  * Function `truncate_diff_for_card(diff_text: str, max_lines: int = 14, max_cols: int = 84) -> FormattedDiff`:
    - Strips common left whitespace indentation.
    - Highlights added lines with `+` (green) and removed lines with `-` (red).
    - **Hard wrap ban:** Never wrap lines. Truncate lines > 84 columns with `…` or fold function signatures.
    - Collapses boilerplate or unchanged lines using semantic ellipsis (`// ... unchanged`).
    - If diff is empty or binary, generates clean metadata card instead of 0-height SVG.
* **Task 4.2: Implement `src/lore/visual/layout_engine.py` & `themes.py`**
  * Bundle `JetBrainsMono-Regular.ttf` inside `src/lore/visual/assets/fonts/`.
  * Inline base64 font in SVG `<defs>` to guarantee identical character metrics on all OS environments.
  * Layout modes:
    - **16:9 (1200x675):** Max 14 lines @ 18px font / 24px line-height.
    - **1:1 (1080x1080):** Max 20 lines @ 20px font / 28px line-height + bottom stat pill (`+LOC/-LOC`, stack tag).
  * WCAG AA contrast check (>4.5:1) for all tokens across Tokyo Night, Catppuccin Mocha, and One Dark.
* **Task 4.3: Implement `src/lore/visual/card_generator.py`**
  * Check for native `freeze` binary in `$PATH`; if present, utilize for accelerated compilation.
  * Try importing `resvg-py` if available; otherwise write pure SVG and inform user to install `lore-cli[visual]`.
  * Target output PNG file size < 600KB.
* **Verification Gate:**
  * Add `tests/test_visual_cards.py`. Test rendering a Python diff into a valid SVG and PNG. Verify aspect ratios and font embedding.

---

### Phase 5: Asynchronous Headless Approval Gateway & Web Dashboard

#### Objective
Enable friction-free approvals. Local users review via a lightweight local dashboard on Port 4748 or CLI; team users approve via Slack/Discord interactive webhooks.

#### Tasks & Acceptance Criteria
* **Task 5.1: Implement `src/lore/approval/local_web.py`**
  * Use `http.server.ThreadingHTTPServer` bound strictly to `127.0.0.1:4748` (avoiding port 4747 home-dashboard conflict).
  * Dynamic port fallback (4748 -> 4749..4755) if occupied.
  * Ephemeral session token query validation (`?token=...`) on all POST routes to prevent CSRF.
  * In-browser slide-over markdown editor with auto-save to eliminate TTY crashes when using CLI `$EDITOR`.
  * Hotkeys: `J`/`K` navigation, `A` (approve), `E` (edit), `C` (copy copy + PNG image to system clipboard), `R` (reject).
* **Task 5.2: Implement `src/lore/approval/slack_gateway.py`**
  * Zero-vendor-SDK: Build Slack Block Kit payloads using existing `httpx` client.
  * Include platform badge, draft copy, attached visual diff image, and evidence commit link.
  * Support `[Approve & Schedule]`, `[Dismiss]`, and `[Approve with Edit]` triggering a native Slack modal.
* **Task 5.3: Implement `src/lore/approval/discord_gateway.py` & `telegram_gateway.py`**
  * Discord webhook dispatcher with rich embeds and button components via `httpx`.
  * Telegram bot webhook with inline keyboard markup and `ForceReply` for mobile 1-tap approvals via `httpx`.
* **Task 5.4: Implement CLI Interactive Reviewer in `src/lore/cli.py`**
  * `lore review` provides interactive terminal TUI (`rich.live`) with identical hotkeys for pure terminal workflows.
* **Verification Gate:**
  * Add `tests/test_approval_gateways.py`.
  * Mock HTTP responses and verify Block Kit and Discord payloads match platform specifications.

---

### Phase 6: Multi-Platform Publishing Engine

#### Objective
Publish approved drafts directly to connected technical channels using `httpx` without external vendor SDK bloat.

#### Tasks & Acceptance Criteria
* **Task 6.1: Implement `src/lore/publishing/social_router.py`**
  * Unified interface `publish_draft(draft_id: str, platform: Platform) -> PublishResult`.
  * Maintain queue state in `publish_queue` table:
    - **429 (Rate Limit):** Extract `Retry-After`; schedule retry for `now() + retry_after`.
    - **5xx / Network Timeout:** Exponential backoff with jitter (max 3 attempts).
    - **401 / 403 / 400:** Mark `status = 'failed'` immediately with `last_error` recorded. Notify user to refresh credentials.
* **Task 6.2: Implement `src/lore/publishing/linkedin.py`**
  * Use versioned Restli Community Management API (`POST https://api.linkedin.com/rest/posts` and `POST https://api.linkedin.com/rest/images?action=initializeUpload` with `LinkedIn-Version: 202401+`).
  * Require `offline_access` scope for 365-day refresh tokens.
  * Text formatter: converts code mentions to unicode monospace (never outputs broken raw backticks into feed).
* **Task 6.3: Implement `src/lore/publishing/bluesky.py`**
  * Direct AT Protocol publishing via `com.atproto.repo.createRecord` using `httpx`.
  * **Exact UTF-8 Byte Offset Slicing:**
    ```python
    text_bytes = post_text.encode("utf-8")
    byte_start = text_bytes.find(target_bytes)
    byte_end = byte_start + len(target_bytes)
    ```
  * Handle DID resolution (`com.atproto.identity.resolveHandle`) for `@mentions`.
  * Blob image upload capped at 1MB with compression.
* **Task 6.4: Implement `src/lore/publishing/github_release.py`**
  * GitHub REST API release generator using `gh` CLI auth or GitHub token.
  * Formats structured markdown (`### Features`, `### Bug Fixes`, `### Architecture Notes`) with commit links and author handles.
* **Task 6.5: Implement `src/lore/publishing/twitter_bridge.py`**
  * 3-tier publisher: Web Intent URL + automated PNG clipboard copy (`wl-copy`/`xclip`/`pbcopy`), Typefully/Buffer webhook bridge, or native BYOK Twitter API v2 client.
* **Verification Gate:**
  * Add `tests/test_publishers.py`.
  * Mock API endpoints for LinkedIn, Bluesky, and GitHub; verify headers, payload structures, and error handling.

---

### Phase 7: Model Context Protocol (MCP) Server for AI IDEs

#### Objective
Allow AI agents in Cursor, Claude Code, Windsurf, and Antigravity to natively inspect project lore and generate drafts via standardized MCP tools.

#### Tasks & Acceptance Criteria
* **Task 7.1: Implement `src/lore/mcp/server.py`**
  * Standard stdio MCP server using Python `mcp` SDK (optional extra) or lightweight JSON-RPC over stdin/stdout.
  * Registered Tools:
    1. `lore_scan`: Scans the current workspace git history.
    2. `lore_list_atoms`: Lists extracted content atoms with evidence links.
    3. `lore_draft`: Generates an anti-slop draft from a specific atom or recent commits.
    4. `lore_render_card`: Generates a syntax-highlighted diff card PNG.
    5. `lore_approve`: Approves and queues a draft for publication.
* **Task 7.2: Register MCP Configuration**
  * Provide configuration snippets for `claude_desktop_config.json` and `.cursor/mcp.json`.
* **Verification Gate:**
  * Add `tests/test_mcp.py` testing JSON-RPC tool calls over stdin/stdout.

---

## 5. Comprehensive Risk Matrix & Defensive Engineering

| Risk / Failure Mode | Severity | Probability | Defensive Counter-Measure |
|---|---|---|---|
| **Social API Rate Limit / Downtime** | High | Medium | Store failed dispatches in `publish_queue` with exponential backoff; never drop user copy. |
| **LinkedIn Token Expiry (60 Days)** | High | High | Run `TokenLifecycleManager` with `offline_access` scope, alerting users 10 days before expiration. |
| **Hex Secret Missed by Entropy Scanner** | Catastrophic | Low | Only whitelist 40-char hex if verified in local Git commit history; enforce variable-name heuristics. |
| **AST Diff Truncation / Overflow** | Medium | Medium | Strict no-wrap ban: max 84 cols, max 14-20 lines; auto-collapse unchanged context with `// ...`. |
| **Slack Webhook Callback Failure (NAT)** | Medium | High | Decouple local free users to `localhost:4748` web dashboard; use cloud relay for Pro/Team. |
| **Port 4747 Collision** | High | High | Re-allocated Lore review server to `4748` with dynamic port fallback (`4748..4755`). |
| **Python 3.14 Native Wheel Failures** | High | Medium | Core packages remain zero-C dependencies; `resvg-py` and `mcp` placed in optional extras with fallbacks. |
| **Existing Test Regressions** | High | High | Retain `is_noise_commit()` contract intact; default `include_wip=False` in `scan_commits()`; default values on all new model fields. |

---

## 6. Execution Verification Protocol

For every phase (Phase 0 through Phase 7), the implementing agent must strictly verify:
1. **Existing Test Suite:** `pytest tests/` must pass 24/24 tests with 0 failures before marking a phase complete.
2. **Offline Isolation:** All unit tests must pass with `LORE_MOCK_LLM=1` without network access or cloud API keys.
3. **Clean Git State:** Commit code changes atomically at the conclusion of each phase with conventional commit messages (`feat:`, `fix:`, `test:`).
