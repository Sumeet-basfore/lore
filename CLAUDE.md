# CLAUDE.md — Developer & Assistant Guidelines for Lore

This document provides quick-start commands, development workflows, and architectural rules for developers and AI assistants working in the **Lore** codebase.

---

## 1. Quick Development Commands

### Environment Setup
```bash
# Navigate to project
cd projects/lore

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

### Running Lore CLI Locally
```bash
# Run CLI directly
lore --help

# Initialize configuration
lore init

# Add a project to watch
lore project add /home/sumeet/personal-repo/projects/veltr --name veltr

# Scan git commits from the last 14 days
lore scan --project veltr --since "14 days ago"

# View extracted content atoms
lore atoms --project veltr

# Generate a social post using local Ollama
lore generate --project veltr --platform twitter

# View, edit, and approve drafts
lore drafts
lore draft show <draft_id>
lore draft approve <draft_id>
lore export --status approved --output-dir ./exports
```

### Running Tests
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_humanizer.py -v
pytest tests/test_scanner.py -v
```

---

## 2. Key Architecture Concepts

1. **Git Scanner (`lore/scanner/`):**
   * Uses git commands to inspect commits, diffs, branches, and tags.
   * Extracts quantitative evidence (files changed, insertions, deletions).
   * Strips out noise (merge commits, typo fixes) and excludes all secrets (`.env`, `.pem`).

2. **Atom Extraction (`lore/extraction/`):**
   * Converts raw git logs into typed **Content Atoms** (`feature`, `bugfix`, `refactor`, `milestone`, `stack_decision`).
   * Couples each atom with an immutable **Evidence Ledger** linking back to specific commit hashes.

3. **Intelligence & Ranking (`lore/intelligence/`):**
   * Computes a `potential_score` (0.0 to 1.0) based on change magnitude, novelty, and narrative tension.

4. **LLM Routing (`lore/generation/router.py`):**
   * Local-first: Connects directly to local Ollama (`http://localhost:11434`) with zero external API key requirements.
   * API-enabled: Easily switches to OpenAI, Anthropic Claude, Gemini, or OpenRouter when keys are configured.

5. **3-Pass Anti-Slop Humanizer (`lore/generation/humanizer.py`):**
   * **Pass 1:** Regex & lexical rules strip 29 known AI writing tells (puffery, AI vocab, copula avoidance, em-dash crutches).
   * **Pass 2:** Voice calibration adjusts cadence, first-person framing, and sentence lengths.
   * **Pass 3:** Adversarial self-audit reviews draft with *"What makes this obviously AI generated?"* and executes surgical correction.

6. **SQLite Storage (`lore/core/database.py`):**
   * Default location: `~/.lore/lore.db`.
   * Manages `projects`, `content_atoms`, `drafts`, and `voice_samples`.

---

## 3. Strict Development Rules

* **Zero AI Cliché Words:** Never allow templates or generation functions to output words like *delve, tapestry, testament, pivotal, intricate, crucial, landscape, vibrant, groundbreaking*.
* **Evidence Tracing:** Every generated post must be backed by a verified Content Atom evidence record.
* **Keep Dependencies Lean:** No heavy web servers or bulky UI libraries. Click, Rich, Pydantic, Jinja2, PyYAML, and HTTPX are the primary core tools.
* **Maintain Test Coverage:** Every new module must have a corresponding test file in `tests/`.
* **Git Commits:** Make descriptive local commits after completing each meaningful slice.

## Design System
Read DESIGN.md before visual or UI work: it defines the fonts, colors, spacing, logo use, and voice. Ask the user before departing from it. When reviewing or QA-ing UI, flag code that doesn't match DESIGN.md.

For public product copy and screenshots, use current beta behavior in README.md, BETA.md, and CONTEXT.md §2. Treat architecture notes in this file as historical where they conflict. Do not claim source diffs are scanned, secrets are fully detected, each draft sentence is verified, content is guaranteed accurate, or Lore publishes posts.
