# Lore (`lore-cli`) v2.0

> Turn your git commits into high-signal engineering content. Zero slop, zero hallucinations.

**Lore** is a CLI-first developer content engine that mines your local git repositories, identifies meaningful engineering accomplishments (features, bugfixes, refactors, milestones), traces every claim with an Evidence Ledger, and synthesizes platform-native social posts, threads, articles, and changelogs using local models (Ollama) or cloud APIs.

Every piece of content passes through an Enterprise DLP scanner, a 2-stage Anti-Slop Humanizer, and an automated Hacker News Critic gate to ensure it sounds like an authentic systems engineer, not corporate marketing copy.

---

## Quick Start

```bash
# 1. Install editable package
pip install -e .

# 2. Initialize configuration (author name, handle, default LLM)
lore init

# 3. Add a project to watch
lore project add /path/to/repo --name myproject

# 4. Scan recent commits and extract content atoms
lore scan --project myproject --since "7 days ago"

# 5. View extracted content atoms and evidence
lore atoms --project myproject

# 6. Generate humanized drafts (uses local Ollama by default)
lore generate --project myproject --platform twitter

# 7. Generate a syntax-highlighted visual diff card (SVG / PNG)
lore card --aspect-ratio 16:9 --theme tokyo_night

# 8. Interactive Review Gateway
# Terminal TUI:
lore review
# Or launch the local web dashboard (http://127.0.0.1:4748):
lore review --web

# 9. Launch Model Context Protocol (MCP) stdio server for Claude Code / Cursor
lore mcp

# 10. Export approved drafts to Markdown or JSON
lore export --status approved --output-dir ./content
```

---

## Core Architecture & Features

- 🛡️ **Enterprise DLP & Shannon Entropy Engine:** 42 Gitleaks-compliant secret patterns plus Shannon entropy analysis ($H \ge 3.75$ for hex, $H \ge 4.8$ for Base64) prevent accidental leakage of API keys, private certificates, JWTs, and AWS tokens. Commits are verified against local git history to avoid false positives on valid SHAs.
- 🌳 **AST Structural Code Inspector:** Language-aware syntax tree parsing (Python `ast`, plus regex grammars for Go, Rust, and TypeScript) isolates function boundaries, deleted lines, and architectural hunks, reducing raw diffs by 82% before LLM ingestion.
- 📜 **Evidence Ledger:** Traces every claim, diff stat, and file reference directly to immutable commit SHAs. No fabricated metrics or hallucinations.
- ✍️ **2-Stage Anti-Slop Humanizer + HN Critic Gate:** Strips 35+ prohibited AI tropes, copula crutches (*"serves as a testament"*), and em-dash spam. The automated Hacker News Critic scores technical credibility on a 1–10 scale, rejecting superficial content.
- 🎨 **Headless Visual Diff Card Generator (`lore card`):** Renders syntax-highlighted code diff cards in SVG and PNG with macOS window chrome and `lore.dev/diff` pill tag. Strict 84-column hard-wrap ban, 14-line (16:9 1200x675) or 20-line (1:1 1080x1080) limits, and WCAG AA contrast compliance across Tokyo Night, Catppuccin Mocha, and One Dark themes.
- 🖥️ **Local Web Review Dashboard (`lore review --web`):** Zero-dependency `ThreadingHTTPServer` bound strictly to `127.0.0.1:4748` (with fallback ports 4749..4755). Monospace dark UI, keyboard hotkeys (`J/K`, `A`, `R`, `E`, `C`), ephemeral CSRF protection, and a slide-over Markdown editor with auto-save.
- 🔌 **Model Context Protocol (MCP) Server (`lore mcp`):** Standard stdio JSON-RPC 2.0 server exposing `lore_scan`, `lore_list_atoms`, `lore_draft`, `lore_render_card`, and `lore_approve` directly inside Cursor, Claude Desktop, Windsurf, and Antigravity.
- 🚀 **Multi-Platform Publishing Router:** Pure `httpx` zero-SDK connectors for LinkedIn Restli v2 (`/rest/posts`), Bluesky AT Protocol (`com.atproto.repo.createRecord` with UTF-8 byte facets), Twitter Web Intent with automatic clipboard card copying, and GitHub Releases.
- 🎙️ **Voice Calibration:** Ingests your own writing samples to tune sentence cadence, paragraph density, and developer voice.
- 🦙 **Local-First & Multi-Model:** Works completely offline with local Ollama (`gemma4`, `qwen3`, `llama3.2`) or cloud providers (`anthropic`, `openai`, `gemini`, `openrouter`).

---

## IDE MCP Integration

### Cursor
Add to your project's `.cursor/mcp.json`:
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
*(If using a Python virtual environment, set `"command": "/path/to/venv/bin/lore"`)*

### Claude Desktop
Add to `claude_desktop_config.json`:
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

---

## Testing & Verification

Lore maintains 100% hermetic unit and integration test coverage across all subsystems:

```bash
# Run the complete test suite (55 tests)
pytest
```

---

## License

MIT © [Sumeet Basfore](https://github.com/Sumeet-basfore)
