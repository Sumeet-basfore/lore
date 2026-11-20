# LORE — Product Requirements Document

**Status:** Implementation Ready  
**Product:** Lore (`lore-cli`)  
**Version:** 1.0.0 Specification  
**Author:** Sumeet Basfore  
**Last Updated:** 2026-11-20  
**Target Package:** `lore-cli` (Python CLI tool)  

---

## 1. Executive Summary & Vision

Developers write code, resolve nasty bugs, architect systems, and ship features every single day. Yet, 95% of this engineering work remains invisible to the public because converting commits and diffs into compelling social media posts, Twitter/X threads, LinkedIn updates, changelogs, and blog articles is tedious, time-consuming, and friction-heavy.

Existing AI tools fail dramatically in this space for two reasons:
1. **Lack of Ground Truth:** They require manual prompting and hallucinate features, statistics, or context because they don't inspect actual code changes.
2. **AI Slop:** They generate robotic, formulaic, sycophantic copy stuffed with clichés (*"In today's fast-paced landscape"*, *"Testament to innovation"*, *"Delve into"*).

**Lore** is a CLI-first, local-first content engine and developer content manager that automatically inspects project directories, scans git history, extracts meaningful "content atoms", traces every claim to real commits via an Evidence Ledger, and synthesizes high-impact, platform-native developer content. Crucially, Lore incorporates an automated **3-Pass Anti-Slop Humanization Engine** that strips 29 distinct AI writing tells, injects authentic developer voice, and calibrates against the developer's personal writing samples.

Lore is fully local-first by default (leveraging local LLMs via Ollama), but seamlessly supports remote API keys (OpenAI, Anthropic, Google Gemini, OpenRouter) with zero code leakage.

---

## 2. Core Personas & Problem Statement

### 2.1 Personas
* **The Solo Indie Hacker / Builder:** Shipping constantly across multiple repos. Has zero time to write marketing copy or social updates, yet knows visibility is necessary for traction.
* **The Open-Source Maintainer:** Needs clear, evidence-backed changelogs, release announcements, and technical deep-dives to attract contributors and users.
* **The Professional Software Engineer:** Wants to build a personal brand and technical credibility on X/LinkedIn without spending hours drafting posts or sounding like a corporate chatbot.
* **The DevRel / Technical Content Creator:** Needs a pipeline to extract story angles from engineering sprints to turn into blog posts and tutorials.

### 2.2 Key Pain Points
* **Context Switching:** Stopping coding to write tweets or articles breaks flow state.
* **Blank Canvas Syndrome:** Developers don't know what makes good content out of their routine commits.
* **AI Hallucinations & Fluff:** Asking ChatGPT to "write a tweet about my project" creates embarrassing AI slop that damages technical credibility.
* **Privacy & Cost:** Sending proprietary source code to cloud AI APIs can violate company policies or incur heavy API token costs.

---

## 3. Product Principles

1. **Evidence Before Copy:** Never fabricate metrics, performance gains, or functionality. Every substantive claim must trace back to a commit hash, diff stat, or verified file path.
2. **Absolute War on AI Slop:** Strip corporate filler, copula avoidance, em-dash crutches, empty adverbs, and superficial participle clauses. Content must sound like a skilled engineer talking to peers.
3. **Local-First & Privacy Preserving:** Operates locally with Ollama by default. Private code stays on machine. Sensitive files (`.env`, secrets, credentials) are strictly ignored.
4. **CLI-First Efficiency:** Powerful, fast, scriptable terminal commands with rich terminal UI; no bloated web dependencies for core workflows.
5. **Human in the Loop:** Lore drafts, indexes, ranks, and suggests; the human approves, edits, and owns the final broadcast.

---

## 4. System Architecture & Information Pipeline

Lore operates as a 5-stage sequential pipeline:

```
[ Git Scanner & Project Walker ]
              ↓
   [ Content Atom Extractor ]
              ↓
  [ Content Intelligence & Ranking ]
              ↓
 [ Multi-Model Generation & 3-Pass Humanizer ]
              ↓
  [ SQLite Draft Store & Terminal Reviewer ]
```

### Stage 1: Git Scanner & Project Walker
* Scans local repository roots or individual projects.
* Parses `git log`, `git diff --stat`, `git tag`, branches, commit timestamps, and author records.
* Inspects `README.md`, package manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`), and documentation for architecture context.
* Filters out merge commits, noise commits (`wip`, `fix typo`), and binary assets.

### Stage 2: Content Atom Extractor
* Groups related commits into cohesive **Content Atoms**:
  - `feature`: Newly implemented user-facing or architectural capability.
  - `bugfix`: Notable bug resolution with reproduction context or subtle fix.
  - `refactor`: Major codebase simplification, performance upgrade, or cleanup.
  - `milestone`: Commit counts, releases, version bumps, or streak milestones.
  - `stack_decision`: New framework, library, or architectural shift.
* Generates an **Evidence Record** linking commit SHAs, file counts, and net diff stats.

### Stage 3: Content Intelligence & Angle Finder
* Scores and ranks atoms based on:
  - Technical complexity / novelty.
  - Relatability to other developers.
  - Narrative potential (problem → struggle → decision → outcome).
  - Platform fit (e.g., quick hot take for X vs. architectural breakdown for LinkedIn).

### Stage 4: Multi-Model Generation & 3-Pass Humanizer
* **LLM Router:** Routes to Ollama (default models: `gemma4:e2b`, `qwen3:4b`, `llama3.2:3b`) or remote APIs (`openai`, `anthropic`, `openrouter`, `gemini`).
* **Prompt Engine:** Platform-specific Jinja2 templates (Twitter/X single post, Twitter thread, LinkedIn post, Dev.to/Markdown blog post, Changelog note).
* **3-Pass Anti-Slop Humanizer Engine:**
  - *Pass 1 (Pattern Strip):* Eliminates 29 documented AI writing patterns (puffery, AI vocabulary, rule-of-three, copula avoidance, passive fragments, title-case headings).
  - *Pass 2 (Voice Calibration):* Matches author writing patterns (sentence cadence, vocabulary, punctuation style) based on stored reference samples.
  - *Pass 3 (Self-Audit & Fix):* Evaluates draft with adversarial prompt *"What makes this obviously AI generated?"* and executes surgical correction.

### Stage 5: SQLite Draft Store & Terminal Reviewer
* Persists projects, scans, content atoms, drafts, and publication states in local SQLite (`~/.lore/lore.db`).
* Interactive CLI commands to list, filter, inspect, edit in `$EDITOR`, approve, reject, or export drafts to Markdown/JSON.

---

## 5. Functional Requirements (P0 / P1 / P2)

### 5.1 Project & Git Repository Management
* **LOR-001 (P0): Project Registry:** Users can register directories to watch (`lore project add <path> --name <name>`).
* **LOR-002 (P0): Git Scan Engine:** Automatically extracts commit logs, diff summaries, file change lists, and release tags within customizable date ranges (`lore scan --since "7 days ago"`).
* **LOR-003 (P0): Secret Exclusion Guard:** Absolute blacklisting of `.env*`, `.pem`, `.key`, credentials, tokens, or private config files from inspection or draft generation.
* **LOR-004 (P1): Multi-Project Batch Scanning:** Scan all registered projects in one sweep (`lore scan --all`).

### 5.2 Content Atom Extraction & Evidence Ledger
* **LOR-010 (P0): Atom Categorization:** Automatically classifies git activity into Features, Bug Fixes, Refactors, Milestones, and Architectural Decisions.
* **LOR-011 (P0): Evidence Ledger:** Stores exact commit hashes, file list, lines added/removed, and authors for each extracted atom. No generated post may assert facts without an evidence link.
* **LOR-012 (P1): Noise Filtering:** Configurable ignore rules for trivial commits (`chore(deps)`, `style:`, `merge branch`).

### 5.3 Multi-Model LLM Routing
* **LOR-020 (P0): Local Ollama Support:** Native zero-dependency HTTP client to `http://localhost:11434/api/generate` and `/api/chat`. Works offline with zero API keys.
* **LOR-021 (P0): Cloud API Providers:** Support for OpenAI, Anthropic Claude, Google Gemini, and OpenRouter via standard environment variables or config keys.
* **LOR-022 (P0): Dynamic Model Switching:** Command-line override for provider and model (`lore generate --model ollama/gemma4:e2b` or `lore generate --model anthropic/claude-3-5-sonnet`).

### 5.4 3-Pass Anti-Slop Humanization Engine
* **LOR-030 (P0): AI Pattern Cleanser:** Removes high-frequency AI words (*delve, tapestry, testament, pivotal, intricate, crucial, landscape, vibrant*), fake balance, and copula avoidance.
* **LOR-031 (P0): Direct Voice & Soul:** Enforces active voice, first-person perspective, concrete numbers over adjectives, and opinions over neutral summaries.
* **LOR-032 (P0): Adversarial Self-Audit:** Automated self-critique pass that detects remaining machine tells and rewrites before presenting draft to user.
* **LOR-033 (P1): Voice Profile Calibration:** User can import 1–5 samples of their genuine writing (`lore voice add <file>`). Extracts cadence, sentence lengths, and preferred idioms.

### 5.5 Platform Generation Formats
* **LOR-040 (P0): Twitter/X Post:** Single tweet under 280 characters with punchy hook, real code metric, and zero hashtag spam.
* **LOR-041 (P0): Twitter/X Thread:** Multi-tweet narrative (3-7 tweets) covering: Hook → Problem Context → Engineering Decision / Code Snippet → Trade-offs → Takeaway.
* **LOR-042 (P0): LinkedIn Post:** 800-1400 characters, clean single-sentence line breaks, professional engineering insight, conversational tone, no fake inspirational tropes.
* **LOR-043 (P0): Developer Blog / Markdown Article:** Structured article with title, executive summary, problem statement, technical solution, code walkthrough, and lessons learned.
* **LOR-044 (P1): User-Facing Changelog:** Translates developer commit jargon into clear, benefit-oriented release notes.

### 5.6 Draft Management & Interactive Review
* **LOR-050 (P0): SQLite Persistence:** Robust local SQLite database storing projects, atoms, drafts, status (`drafted`, `approved`, `rejected`, `published`), and timestamps.
* **LOR-051 (P0): Terminal Inspection & Approval:** Rich CLI table displaying drafts, single-draft inspection, and state transition (`lore draft approve <id>`).
* **LOR-052 (P0): Direct Editor Integration:** Opens draft in user's `$EDITOR` (`nano`, `vim`, `code`) for instant human refinement (`lore draft edit <id>`).
* **LOR-053 (P0): Export Capabilities:** Export approved drafts to markdown files or directory bundles (`lore export --status approved --out ./content`).

---

## 6. Anti-Slop Specifications (Strict Rulebook)

The generator and humanizer must strictly adhere to the following rules:

| Category | Forbidden AI Tell | Lore Humanized Alternative |
|---|---|---|
| **Puffery** | "a pivotal moment", "testament to innovation", "revolutionary" | State exact fact: "shipped v1.2 with 3 new endpoints" |
| **Vocabulary** | *delve, intricate, crucial, tapestry, leverage, utilize, seamless* | Plain English: *dig into, complex, important, use, direct* |
| **Copula Avoidance** | "serves as a foundation", "stands as a solution" | Direct copula: "is", "has", "does" |
| **Participle Fluff** | "...highlighting the importance of testing, ensuring safety" | Full clause or delete: "This prevented database lockups." |
| **Negative Parallel**| "It's not just about speed, it's about reliability." | Direct statement: "Reliability mattered more than raw speed." |
| **False Ranges** | "From startup founders to enterprise architects..." | Specific: "Engineers using Postgres in production" |
| **Punctuation** | Em-dash spam (`—`), excessive colon connectors | Short periods, natural commas, or new sentences |
| **Chatbot Artifacts**| "Here is your post!", "I hope this helps!", "Let's dive in!" | Zero chatbot preamble; return only publishable copy |
| **Hedging** | "It could potentially possibly be argued that..." | "In our testing, memory dropped 30%." |

---

## 7. Data Models & Schemas

### 7.1 Database Schema (SQLite)

```sql
-- Projects watched by Lore
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL UNIQUE,
    description TEXT,
    tech_stack TEXT, -- JSON array
    last_scanned_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content Atoms extracted from Git & Code analysis
CREATE TABLE content_atoms (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    atom_type TEXT NOT NULL, -- feature, bugfix, refactor, milestone, stack_decision
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence TEXT NOT NULL, -- JSON: { commits: [], files_changed: 0, insertions: 0, deletions: 0, date_range: [] }
    tech_stack TEXT, -- JSON array
    potential_score REAL DEFAULT 0.5,
    status TEXT DEFAULT 'unprocessed', -- unprocessed, drafted, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generated Content Drafts
CREATE TABLE drafts (
    id TEXT PRIMARY KEY,
    atom_id TEXT REFERENCES content_atoms(id) ON DELETE SET NULL,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- twitter, twitter_thread, linkedin, blog, changelog
    title TEXT,
    raw_content TEXT NOT NULL,
    humanized_content TEXT NOT NULL,
    humanizer_audit TEXT, -- JSON notes from self-audit
    status TEXT DEFAULT 'drafted', -- drafted, approved, rejected, published
    published_url TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice Profile Samples
CREATE TABLE voice_samples (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    analysis TEXT, -- JSON: { avg_sentence_len, tone, idioms, punctuation_profile }
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. CLI Command Specifications

```bash
# Setup & Configuration
lore config list                       # Show current configuration
lore config set <key> <value>          # Set config (e.g. llm.provider, default_model)
lore init                              # Interactive onboarding & initial config

# Project Management
lore project add <path> [--name <name>]# Register repository
lore project list                      # List watched repositories
lore project remove <name>             # Unregister repository

# Scanning & Extraction
lore scan [--project <name>] [--since "7d"] # Scan git repos for new commits
lore atoms [--project <name>]          # View extracted content atoms

# Generation
lore generate [--project <name>]       # Generate drafts from top atoms
              [--atom <id>]            # Generate from specific atom
              [--platform <platform>]  # twitter | thread | linkedin | blog | changelog
              [--model <model>]        # Override LLM model

# Voice Calibration
lore voice add <file.md>               # Ingest personal writing sample
lore voice list                        # List active samples
lore voice analyze                     # Compute aggregate voice profile

# Draft Workflow
lore drafts [--status drafted|approved] # List drafts in rich terminal table
lore draft show <id>                   # Display full draft and evidence
lore draft edit <id>                   # Open in $EDITOR
lore draft approve <id>                # Mark approved for publishing
lore draft reject <id>                 # Reject / archive draft

# Export
lore export [--status approved]        # Export to markdown files
            [--format json|markdown]
            [--output-dir <path>]
```

---

## 9. Monetization Roadmap

### Phase 1: Open Source Developer CLI (Immediate)
* 100% free, MIT licensed, local-first.
* Drives initial adoption, organic GitHub stars, developer trust, and real-world feedback.

### Phase 2: Pro CLI Subscription ($9–$19/month)
* **Direct Auto-Publishing:** Official API integrations for X/Twitter, LinkedIn, Dev.to, Hashnode, Medium.
* **Auto-Schedule Queue:** Intelligent scheduling algorithm posting at optimal engagement windows.
* **Performance Telemetry:** Ingest view, like, and repost metrics to automatically fine-tune future hook formulas.
* **Advanced Multi-Repo Sync:** Scheduled background daemons watching enterprise repos.

### Phase 3: Lore Cloud / Web Dashboard ($29–$79/month)
* Web-based visual content studio and team kanban.
* Team workspaces: Agency or startup founders managing multiple developers/engineers.
* GitHub App / GitLab Webhooks: Automatically drafts content upon PR merge or tag release.
* Hosted LLM inference with specialized fine-tuned developer voice models.

### Phase 4: Enterprise Engineering Advocacy ($299+/month)
* Organization-wide Developer Advocacy Platform.
* Automated engineering brand building across an entire company's developer base.
* Compliance and IP guardrails ensuring no proprietary algorithms or private intellectual property leak into posts.

---

## 10. Success Metrics & Verification Criteria

1. **Extraction Accuracy:** 100% of generated claims must match git commit evidence.
2. **Anti-Slop Quality:** Zero occurrence of the 29 prohibited AI writing tells in final humanized drafts.
3. **Local Usability:** `lore scan` and `lore generate` must execute end-to-end on a clean machine using local Ollama without requiring external internet or API keys.
4. **Execution Speed:** Git scan of a 1,000-commit repository must complete in under 2 seconds.
5. **Robustness:** 100% test coverage on scanner, parser, evidence ledger, humanizer rules, and database schema migrations.
