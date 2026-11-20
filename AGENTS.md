# AGENTS.md — Lore Engineering Instructions

This document is the operational contract for any AI coding agent working inside the **`projects/lore`** repository. Read this file completely before creating or editing files. The authoritative product specification is [`PRD.md`](./PRD.md).

---

## 1. Core Mission & Philosophy

You are building **Lore** (`lore-cli`), a CLI-first, local-first developer content engine and social media content generator. Lore mines git repositories for real changes, creates verifiable content atoms, routes through local or API-backed LLMs, and subjects every draft to an uncompromising 3-pass anti-slop humanization pipeline.

**Core Mandates:**
* **Truth over Hype:** Never invent metrics, performance claims, or fake testimonials. All facts must trace directly to git commits or file trees.
* **Ruthless Anti-Slop:** Every single piece of generated prose must pass through the anti-slop rules codified in the Humanizer specification. AI cliché vocabulary (*delve, tapestry, crucial, pivotal, landscape, testament*) is strictly forbidden.
* **Local-First & Offline Capable:** The primary target is Ollama running locally. Remote APIs (Anthropic, OpenAI, OpenRouter) are first-class alternatives, but local execution must never be treated as secondary.
* **Clean, Modular Python:** Written in modern Python (3.12+), fully type-annotated, using Click for CLI, SQLite for persistence, and Rich for terminal formatting.

---

## 2. Non-Negotiable Engineering Rules

1. **Do Not Touch Parent Files:** Stay strictly inside `projects/lore/`. Never edit or touch files in `../../` (the parent personal-repo) unless explicitly instructed.
2. **Zero Credentials in Code or Output:** Never log, print, or commit API keys, `.env` contents, or sensitive developer credentials.
3. **Atomic Git Commits:** Keep git history in `projects/lore/` clean and incremental. Make a distinct local commit after completing each feature slice or bug fix.
4. **Read Before Editing:** Always read existing source files and surrounding code before modifying. Match existing architectural patterns.
5. **No Speculative Bloat:** Do not add heavy web servers, React frontends, Docker dependencies, or complex microservices. This is a fast, lightweight, standalone Python CLI tool.
6. **Verify Every Step:** Never declare a feature "done" without executing unit tests or CLI smoke verification.

---

## 3. Architecture & Code Layout

```text
projects/lore/
├── PRD.md                       # Product Requirements Document
├── AGENTS.md                    # This operational contract
├── CLAUDE.md                    # Developer & assistant guidelines
├── CONTEXT.md                   # Strategic business & technical context
├── pyproject.toml               # Poetry/pip/uv build definition & dependencies
├── .gitignore                   # Ignore .venv, __pycache__, .lore/, db files
├── src/
│   └── lore/
│       ├── __init__.py          # Package metadata & version
│       ├── cli.py               # Click CLI entrypoint & subcommands
│       ├── config.py            # Configuration loader (~/.lore/config.yml)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── database.py      # SQLite connection & schema initializer
│       │   ├── models.py        # Pydantic data models (Project, Atom, Draft)
│       │   └── exceptions.py    # Custom domain exceptions
│       ├── scanner/
│       │   ├── __init__.py
│       │   ├── git_scanner.py   # Git log & diff extraction (GitPython/git CLI)
│       │   ├── project_walker.py# Repo structure, README & stack detection
│       │   └── filters.py       # Commit noise & secret filtering
│       ├── extraction/
│       │   ├── __init__.py
│       │   ├── atom_extractor.py# Groups commits into typed Content Atoms
│       │   └── evidence.py      # Computes evidence ledger & stats
│       ├── intelligence/
│       │   ├── __init__.py
│       │   ├── angle_finder.py  # Scores & ranks atoms by narrative value
│       │   └── calendar.py      # Content scheduling & cadence recommendations
│       ├── generation/
│       │   ├── __init__.py
│       │   ├── router.py        # LLM Router (Ollama native HTTP + APIs)
│       │   ├── humanizer.py     # 3-Pass Anti-Slop & Soul Injection engine
│       │   ├── voice.py         # Voice profile analysis & matching
│       │   └── prompts/         # Jinja2 prompt templates
│       │       ├── twitter.j2
│       │       ├── thread.j2
│       │       ├── linkedin.j2
│       │       ├── blog.j2
│       │       └── changelog.j2
│       └── publishing/
│           ├── __init__.py
│           ├── exporter.py      # Export to Markdown & JSON
│           └── clipboard.py     # Copy to system clipboard
└── tests/
    ├── conftest.py              # Pytest fixtures & mock git repository
    ├── test_scanner.py          # Git scanning & filtering tests
    ├── test_extraction.py       # Content atom grouping & evidence tests
    ├── test_humanizer.py        # Anti-slop pattern stripping tests
    ├── test_router.py           # Local Ollama & API routing tests
    └── test_cli.py              # Click runner CLI integration tests
```

---

## 4. Module Boundaries & Responsibilities

### `lore.scanner`
* Responsible for reading git repositories via local `git` CLI or `GitPython`.
* Extracts commits between date ranges, tags, or commit counts.
* Computes diff stats (insertions, deletions, files modified).
* Filters out sensitive files (`.env`, secrets, `.pem`, `.key`) and noise commits (`merge`, `wip`).

### `lore.extraction`
* Transforms raw commit lists into semantic **Content Atoms**:
  - `feature`: new capabilities.
  - `bugfix`: fixed issues.
  - `refactor`: structural or performance cleanups.
  - `milestone`: commit counts, release tags.
  - `stack_decision`: dependency additions / architecture changes.
* Produces an immutable `evidence` dictionary linking commits to claims.

### `lore.intelligence`
* Ranks atoms based on narrative strength, diff magnitude, and platform suitability.
* Prepares ranked story briefs for the generator.

### `lore.generation`
* **`router.py`**: Clean, lightweight client for Ollama (using native HTTP `requests`/`httpx` to `http://localhost:11434/api/generate`) and remote providers (`litellm` or direct provider clients).
* **`humanizer.py`**: Implements the 3-pass pipeline:
  1. *Pattern Strip:* Regex and rule-based scrubbing of the 29 prohibited AI markers.
  2. *Voice Injection:* Applying author rhythm, contractions, and first-person perspective.
  3. *Adversarial Self-Audit:* Querying the LLM with *"What makes this obviously AI generated?"* and performing a final polish pass.
* **`voice.py`**: Parses user-supplied markdown/text samples to compute cadence, vocabulary range, and stylistic traits.

### `lore.core` & `lore.publishing`
* Manages local SQLite storage at `~/.lore/lore.db`.
* Handles atomic migrations, CRUD operations on projects, atoms, and drafts.
* Provides markdown export and terminal output rendering using `Rich`.

---

## 5. Coding & Style Conventions

* **Language:** Python 3.12+ (compatible with Python 3.14).
* **Typing:** Strict type hints (`from typing import Optional, List, Dict`, etc.).
* **Formatting:** Clean PEP 8 formatting.
* **Error Handling:** Use custom domain exceptions (`LoreError`, `GitScannerError`, `LLMRouteError`). Never swallow exceptions silently.
* **CLI UX:** Every command must output informative, beautiful Rich formatting (colors, tables, panels, progress spinners where appropriate).
* **Dependencies:** Keep dependencies minimal:
  - `click` (CLI framework)
  - `rich` (terminal formatting)
  - `pydantic` (data schemas)
  - `jinja2` (prompt templating)
  - `pyyaml` (configuration)
  - `httpx` (async/sync HTTP for Ollama and APIs)
  - `pytest` (testing)

---

## 6. Anti-Slop Enforcement Guidelines

When generating or editing prompt templates and humanizer functions:
1. **Never use AI marker words:**
   `delve`, `tapestry`, `testament`, `pivotal`, `intricate`, `crucial`, `landscape`, `vibrant`, `fostering`, `underscoring`, `seamless`, `groundbreaking`, `revolutionary`.
2. **Ban copula avoidance:**
   Transform *"serves as a solution"* → *"is a solution"*; *"stands as a testament"* → *"shows"*.
3. **No negative parallelism:**
   Ban *"It's not just about X, it's about Y"*.
4. **No rule-of-three padding:**
   Never artificially force points into triplets.
5. **No decorative emoji bullets:**
   Ban `🚀 Launch:`, `💡 Insight:`, `✅ Next Steps:`.
6. **No robotic signposting:**
   Ban *"Let's dive in"*, *"Without further ado"*, *"Here's what you need to know"*.

---

## 7. Working Workflow for Agents

1. **Vertical Slices:** Implement feature by feature in logical slices:
   - Slice 1: Project setup (`pyproject.toml`, database schema, config loader).
   - Slice 2: Git scanner & project walker.
   - Slice 3: Content atom extraction & evidence ledger.
   - Slice 4: LLM router (local Ollama + fallback) & Jinja2 prompt engine.
   - Slice 5: 3-pass anti-slop humanizer engine & voice profile.
   - Slice 6: Full Click CLI integration (`init`, `project`, `scan`, `generate`, `drafts`, `export`).
   - Slice 7: End-to-end unit and integration test suite.
2. **Commit after each verified slice:**
   Run `git add -A && git commit -m "feat(<module>): description"` inside `projects/lore/`.
3. **Run tests before moving on:**
   Ensure all pytest tests pass cleanly before completing.
