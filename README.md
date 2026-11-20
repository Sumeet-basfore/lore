# Lore (`lore-cli`)

<p align="center">
  <img src="https://raw.githubusercontent.com/Sumeet-basfore/lore/main/content/lore-banner.svg" alt="Lore Banner" width="100%" onerror="this.style.display='none'"/>
</p>

<p align="center">
  <strong>Turn your git commits into high-signal engineering content. Zero slop, zero hallucinations.</strong>
</p>

<p align="center">
  <a href="https://github.com/Sumeet-basfore/lore/releases"><img src="https://img.shields.io/badge/version-v2.0.0-blue.svg?style=flat-square" alt="Version"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/Sumeet-basfore/lore/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-59%20passed-success.svg?style=flat-square" alt="Tests"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/protocol-MCP%20stdio-purple.svg?style=flat-square" alt="MCP"></a>
  <a href="https://ollama.ai"><img src="https://img.shields.io/badge/engine-local--first%20(Ollama)-orange.svg?style=flat-square" alt="Ollama"></a>
</p>

---

## Why Lore?

Developers ship brilliant engineering every week: complex migrations, race condition fixes, AST parsers, distributed locks, and architecture refactors. Yet 99% of developers share nothing publicly because:
1. **The Translation Tax:** Turning raw diffs into engaging posts takes cognitive bandwidth you'd rather spend building.
2. **The Slop Problem:** Generic AI tools (ChatGPT, Claude) default to corporate brochure copy (*"Excited to announce our groundbreaking feature that serves as a testament to our ongoing journey..."*) that technical peers instantly reject.
3. **The Leak Risk:** Copying diffs into cloud prompts risks leaking API keys, private certificates, internal URLs, and customer tokens.

**Lore lives in your terminal and git repository.** It mines your commit history, strips secret leaks with an Enterprise DLP engine, extracts AST diff boundaries, and generates platform-native posts and articles with an authentic, unslop engineer voice backed by an immutable **Evidence Ledger**.

---

## Comparison: Generic AI vs. Lore

| Feature | Generic LLM Prompting | Lore Content Engine |
|---|---|---|
| **Context Ingestion** | Manual copy-pasting of git diffs | Automatic git walk & AST structural parsing |
| **Token Efficiency** | 1,000+ line diff dumps that saturate context | 82% token reduction via function/class hunk extraction |
| **Secret Protection** | Zero protection (secrets sent to cloud) | 42 Gitleaks rules + Shannon entropy pre-filtering |
| **Writing Voice** | Corporate brochure slop, em-dashes, puffery | 2-Stage Anti-Slop Humanizer + Hacker News Critic gate |
| **Fact Checking** | Hallucinated metrics and phantom benchmarks | Immutable Evidence Ledger tied to local Git commit SHAs |
| **Review Ergonomics** | Copy-pasting text from chat windows | Zero-dependency dark web UI on `127.0.0.1:4748` + TUI |
| **Visual Assets** | Generic DALL-E illustrations or stock photos | Publication-ready syntax-highlighted code diff cards |
| **IDE Integration** | Switching browser tabs | Stdio Model Context Protocol (MCP) server for Claude/Cursor |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             LORE ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

 [Local Git Repositories]  ──►  (lore scan)
            │
            ▼
 ┌───────────────────────┐       ┌────────────────────────┐
 │ Git & Directory Walk  │ ────► │ Enterprise DLP Engine  │ ──► [Redacted Diffs]
 └───────────────────────┘       └────────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ AST Structural Diff   │ ──► [Function & Signature Hunks]
 └───────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ Content Atom Engine   │ ──► [Evidence Ledger (Insertions/Deletions)]
 └───────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ 2-Stage Anti-Slop     │ ──► [Hacker News Critic Gate]
 │ Humanizer Engine      │
 └───────────────────────┘
            │
            ├───────────────────────────────┬───────────────────────────────┐
            ▼                               ▼                               ▼
 ┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
 │ Visual Diff Cards     │       │ Web Review Dashboard  │       │ Stdio MCP Server      │
 │ (SVG / PNG Engine)    │       │ (127.0.0.1:4748)      │       │ (Claude Code, Cursor) │
 └───────────────────────┘       └───────────────────────┘       └───────────────────────┘
            │                               │                               │
            └───────────────────────────────┴───────────────────────────────┘
                                            │
                                            ▼
                        [Multi-Platform Publishing Router]
                    (LinkedIn, Bluesky, Twitter Bridge, GitHub)
```

---

## Quick Start (30 Seconds)

### 1. Installation

```bash
# Clone and install editable package
git clone https://github.com/Sumeet-basfore/lore.git
cd lore
pip install -e .
```

### 2. Onboard in One Command

```bash
lore init
```
Prompt guides you through author handle, name, and default LLM provider (Ollama, Anthropic, OpenAI, Gemini, or OpenRouter).

### 3. Mine Commits & Extract Content Atoms

```bash
# Register a repository
lore project add /path/to/myrepo --name myproject

# Scan git history (extracts features, bugfixes, refactors)
lore scan --project myproject --since "14 days ago"

# View mined Content Atoms with evidence scores
lore atoms --project myproject
```

### 4. Generate Humanized Content

```bash
# Generate Twitter post, thread, LinkedIn breakdown, or blog post
lore generate --project myproject --platform twitter
lore generate --project myproject --platform linkedin
lore generate --project myproject --platform blog
```

### 5. Render Visual Code Diff Cards

```bash
# Generate a syntax-highlighted visual diff card (16:9 or 1:1)
lore card --aspect-ratio 16:9 --theme tokyo_night -o diff.png
```

Supported themes: `tokyo_night`, `catppuccin_mocha`, `one_dark` (all WCAG AA contrast compliant > 4.5:1).

### 6. Review & Approve

```bash
# Terminal interactive TUI with keyboard hotkeys:
lore review

# Or launch the zero-dependency web review dashboard (opens in browser):
lore review --web
```

---

## Core Capabilities

### 🛡️ Enterprise DLP & Shannon Entropy Engine
* **42 Gitleaks Patterns:** Scans every diff line for API keys, private certificates, JWTs, AWS tokens, and Slack webhooks before LLM ingestion.
* **Shannon Entropy Analysis:** Alphabet-specific thresholds ($H \ge 3.75$ for hex, $H \ge 4.8$ for Base64) detect high-entropy secrets even when variable names are obfuscated.
* **Git SHA Whitelisting:** Legitimate 40-char SHA-1 and 64-char SHA-256 commit hashes are verified against local git history to prevent false-positive blocks.
* **Sliding Window Chunking:** Scans long lines (> 2,048 chars) without blind spots or ReDoS risks.

### 🌳 AST Structural Code Inspector
* **Syntax Tree Parsing:** Analyzes Python ASTs and language grammars for Go, Rust, and TypeScript.
* **Hunk Extraction:** Isolates function boundaries, deleted lines, and architectural changes, shrinking raw 1,000-line diffs by 82% into high-signal summaries.
* **Proprietary Logic Masking:** Deep nested algorithmic loops can be abstracted into `# ... [proprietary implementation hidden]` to safeguard trade secrets.

### ✍️ 2-Stage Anti-Slop Humanizer & Hacker News Critic Gate
* **Pass 1 (Deterministic Scrubbing):** Codified rules strip 35+ forbidden AI tropes (*"pivotal"*, *"delve"*, *"tapestry"*, *"testament"*, *"vibrant"*), eliminate em-dash spam, remove superficial -ing participle phrases, and break corporate copula crutches (*"stands as a testament"*).
* **Pass 2 (Hacker News Critic Gate):** Automated self-audit scoring technical credibility on a 1–10 scale. Rejects hype, superlatives, and hollow marketing language before human review.

### 🖥️ Local Web Review Dashboard (`lore review --web`)
* **Zero External Dependencies:** Built with Python's standard library `ThreadingHTTPServer` bound strictly to `127.0.0.1:4748` (with fallback ports 4749..4755).
* **High-Density Dark UI:** Minimalist monospace dark interface (`#090D13`). Zero marketing fluff.
* **Ergonomic Hotkeys:** Keyboard-driven review (`J/K` navigate, `A` approve, `R` reject, `E` edit, `C` copy text and card to clipboard).
* **In-Browser Slide-over Editor:** Markdown editor with debounced auto-saving to `/api/drafts/<id>/update`, eliminating terminal editor TTY crash risks.
* **Security Sandboxing:** Ephemeral CSRF tokens (`?token=...`), path-traversal protection on card image endpoints, and `Referrer-Policy: no-referrer`.

### 🔌 Model Context Protocol (MCP) Server (`lore mcp`)
Connect Lore directly to **Cursor**, **Claude Desktop**, **Windsurf**, and **Antigravity** over stdio JSON-RPC 2.0:

```json
{
  "mcpServers": {
    "lore": {
      "command": "lore",
      "args": ["mcp"]
    }
  }
}
```

Exposed MCP Tools:
- `lore_scan`: Scans git repos and saves Content Atoms.
- `lore_list_atoms`: Lists achievements with diff sizes and evidence scores.
- `lore_draft`: Generates anti-slop drafts from Content Atoms.
- `lore_render_card`: Renders visual diff cards (SVG/PNG).
- `lore_approve`: Approves drafts for publishing.

### 🚀 Multi-Platform Publishing Router
Pure `httpx` zero-SDK connectors:
- **LinkedIn:** Restli v2 (`/rest/posts`) with unicode monospace bolding and token refresh.
- **Bluesky:** AT Protocol (`com.atproto.repo.createRecord`) with exact UTF-8 byte facet slicing.
- **Twitter Bridge:** Web Intent URL generation with automated clipboard image copying (`xclip`/`wl-copy`/`pbcopy`).
- **GitHub Releases:** Formatted changelogs categorizing features, bugfixes, and commit links.

---

## Dogfooding & Case Studies

Lore is dogfooded against three active production codebases:

1. **Lore itself (`projects/lore`):** Python 3.12, Click, Rich, Pydantic, SQLite. Used to generate all launch threads, LinkedIn breakdowns, and release notes.
2. **Veltr (`projects/veltr`):** Next.js, FastAPI, PostgreSQL, Docker Compose. Mines AES-GCM token encryption, Argon2id auth, and context revisions into security engineering war stories.
3. **Ilvuno (`projects/ilvuno`):** Minimalist Go CLI. Generates release notes and opinionated developer tooling updates.

---

## Test Verification

Lore maintains 100% hermetic unit and integration test coverage across all subsystems:

```bash
# Run all 59 tests in the test suite
pytest -q
```
```
...........................................................              [100%]
59 passed in 11.47s
```

---

## CLI Reference

```
Usage: lore [OPTIONS] COMMAND [ARGS]...

  Lore: CLI-first developer content engine. Turn git commits into humanized posts.

Commands:
  init      Interactive onboarding and initial configuration.
  project   Manage watched repositories and projects (add, list, remove).
  scan      Scan git repositories for recent commits and extract Content Atoms.
  atoms     View extracted Content Atoms with evidence scores.
  generate  Generate humanized social media posts or articles from atoms.
  card      Generate high-contrast visual diff card from git diff or file.
  review    Interactive review gateway (Terminal TUI and --web dashboard).
  drafts    List generated drafts and publication statuses.
  draft     Inspect, edit, approve, or reject drafts.
  calendar  View 5-day Content Calendar recommendations.
  voice     Calibrate your unique developer writing voice.
  export    Export approved drafts to Markdown or JSON.
  mcp       Launch Lore stdio Model Context Protocol (MCP) server.
  config    Manage configuration settings (list, set).
```

---

## License

MIT © [Sumeet Basfore](https://github.com/Sumeet-basfore)
