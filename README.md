# Lore (`lore-cli`)

> Turn your code into content. Zero slop, zero hallucinations.

**Lore** is a CLI-first developer content engine that mines your local git repositories, identifies meaningful engineering achievements (features, bugfixes, refactors, milestones), traces every claim with an Evidence Ledger, and synthesizes platform-native social posts, threads, articles, and changelogs using local models (Ollama) or cloud APIs.

Every piece of content passes through a 3-pass Anti-Slop Humanization pipeline to sound like an authentic engineer, not AI marketing copy.

## Quick Start

```bash
# Install editable package
pip install -e .

# Initialize config
lore init

# Add a project to watch
lore project add /path/to/repo --name myproject

# Scan recent commits and extract content atoms
lore scan --project myproject --since "7 days ago"

# View extracted content atoms
lore atoms --project myproject

# Generate humanized drafts (uses local Ollama by default)
lore generate --project myproject --platform twitter

# View, edit, and approve drafts
lore drafts
lore draft show <id>
lore draft approve <id>
lore export --status approved --output-dir ./content
```

## Features

- 🔍 **Git & Directory Scanner:** Extracts commits, diff stats, file lists, and tech stack detection without sending private code to the cloud.
- 🧬 **Content Atom Extractor:** Groups related commits into Features, Bugfixes, Refactors, Milestones, and Architectural Decisions.
- 📜 **Evidence Ledger:** Traces every claim directly to commit SHAs. No fabricated metrics.
- 🛡️ **3-Pass Anti-Slop Engine:** Removes 29 known AI writing markers, copula avoidance, and em-dash spam.
- 🎙️ **Voice Calibration:** Ingests your own writing samples to match your unique sentence cadence and tone.
- 🦙 **Local-First & Multi-Model:** Works offline with Ollama (`gemma4`, `qwen3`, `llama3.2`) or cloud APIs (`anthropic`, `openai`, `openrouter`, `gemini`).
- 💾 **SQLite Persistence:** All projects, atoms, drafts, and approval states stored locally in `~/.lore/lore.db`.
