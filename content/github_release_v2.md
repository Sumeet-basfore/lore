# Lore v2.0.0 Release Notes

Lore v2.0.0 transitions the project from a command-line prototype into a full local-first developer content engine. 

This release adds AST-aware diff parsing, an enterprise DLP scanner with Shannon entropy checks, headless code-to-image diff card rendering, a zero-dependency local web dashboard, and a native Model Context Protocol (MCP) server for Claude Desktop and Cursor.

All changes adhere to our core philosophy: 100% local-first execution on loopback, zero telemetry, and zero unverified AI marketing copy.

---

## What Changed in v2.0.0

### Database Migration Engine (Commit `e111c43`)
* **Schema Evolution:** Implemented automatic migrations using SQLite `PRAGMA user_version` to upgrade existing v1 databases to v2 cleanly.
* **New Tables:** Added `dlp_audit_logs` for tracking security scans and `publish_queue` for scheduling social posts.
* **New Model Fields:** Extended `Draft` with `card_image_path`, `dlp_status`, `dlp_audit_json`, `scheduled_for`, and `channel_target`.
* **Platform Extensions:** Added native enum support for `Platform.BLUESKY` and `Platform.GITHUB`.

### AST-Aware Semantic Diff Extraction
* **Syntax Tree Parsing:** Replaced raw line-by-line diff processing with Python standard library `ast` parsing and language declaration tokenizers for Go, TypeScript, and Rust.
* **Semantic Summaries:** Extracts modified function signatures, newly handled exceptions, database schema changes, and test assertions instead of passing 1,000 raw diff lines to language models.
* **Commit Clustering:** Groups related commits within 4-hour temporal windows, resolving the "clean commit fallacy" by ignoring intermediate `wip` commits and focusing on the combined architectural diff.

### Local-First Enterprise DLP and Entropy Scanner (Commit `5b9fd25`)
* **Gitleaks Pattern Coverage:** Integrates 42 regular expression patterns detecting AWS credentials, GitHub personal access tokens, private keys, database connection strings, and webhook URLs.
* **Two-Tier Policy:** Enforces Tier 1 Hard Block (zero bytes transmitted) for private key blocks and Tier 2 Masking (`[MASKED_<TYPE>]`) for inline credentials.
* **Shannon Entropy Thresholding:** Evaluates contiguous tokens of length >= 24. Flags Base16 hex tokens with entropy >= 3.75 and Base64/ASCII tokens with entropy >= 4.8.
* **Git SHA Whitelisting:** Cross-references 40-character hexadecimal strings against the local git object database to prevent false positive flags on valid commit hashes.
* **ReDoS Protection:** Discards lines exceeding 2,048 characters prior to regex evaluation.
* **Trade Secret Protection:** Masks internal AST loop bodies with `// ... [proprietary implementation hidden]` to prevent leaking proprietary algorithms.

### Headless Visual Diff Card Engine
* **Code-to-Image Generation:** Generates publication-ready syntax diff cards in SVG and PNG formats at 1200x675 (16:9) or 1080x1080 (1:1).
* **Strict Formatting Constraints:** Hard limit of 84 columns with ellipsis truncation, maximum 14 lines for 16:9 cards, and automatic context folding with `// ... unchanged` markers.
* **Accessible Themes:** Includes Tokyo Night, Catppuccin Mocha, and One Dark themes calibrated for WCAG AA contrast ratio (> 4.5:1).
* **Rasterizer Fallback Chain:** Prefers `freeze` CLI, falls back to `resvg-py`, and defaults to standalone SVG.

### Local Web Review Dashboard
* **Zero-Dependency Server:** Runs on `127.0.0.1:4748` using Python's native `http.server.ThreadingHTTPServer` with fallback ports 4749..4755.
* **Security Guardrails:** Requires an ephemeral CSRF token on every request. Rejects all non-loopback connections.
* **Ergonomics:** Monospace dark interface with keyboard shortcuts (J/K navigation, A approve, R reject, E edit, C copy) and a slide-over Markdown editor with debounced auto-save.
* **Team Gateways:** Supports outbound webhook notifications for Slack Block Kit, Discord embeds, and Telegram inline keyboards.

### Multi-Platform Publishing Engine
* **Pure HTTP Adapters:** Pure `httpx` implementations without third-party vendor SDKs.
* **Supported Targets:**
  * LinkedIn Restli v2 API (`/rest/posts`)
  * Bluesky AT Protocol (`com.atproto.repo.createRecord`) with exact UTF-8 byte offset facets
  * Twitter Bridge via Web Intent and local clipboard integration (`xclip`, `wl-copy`, `pbcopy`)
  * GitHub Releases generator with formatted changelogs linked to commit SHAs

### Model Context Protocol (MCP) Server
* **Native Integration:** Runs a stdio JSON-RPC 2.0 server using `lore mcp`.
* **Tools Exposed:** `lore_scan`, `lore_list_atoms`, `lore_draft`, `lore_render_card`, and `lore_approve`.
* **Editor Configs:** Compatible out of the box with Claude Desktop and Cursor.

---

## Upgrade Instructions

### Updating the Package

Pull the latest source and install the editable package:

```bash
git pull origin main
pip install -e .
```

### Running Migrations

Database migrations execute automatically on your next command. To verify your current schema version:

```bash
lore config list
```

Your database will report `schema_version = 2`.

---

## Breaking Changes

1. **`Platform` Enum:** The internal representation of platforms has been normalized to lowercase strings. If you maintain custom scripts querying SQLite directly, update any manual `WHERE platform = 'TWITTER'` filters to lowercase `twitter`.
2. **Configuration Path:** In earlier beta releases, config could be read from `.lorerc`. In v2.0.0, configuration is read strictly from `~/.lore/config.yml` or the path specified in `LORE_HOME`.

---

## Verification and Test Coverage

The full test suite passed prior to release tagging:
* 50+ unit and integration tests across 12 test modules with zero regressions.
* 100% test pass rate on SQLite migrations, git scanners, AST diffing, DLP filters, humanizers, diff cards, local web server, and CLI flows.
* Verified offline with local Ollama (`gemma4:e2b`) and hermetic mock mode (`LORE_MOCK_LLM=1`).
