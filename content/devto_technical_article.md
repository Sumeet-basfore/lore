---
title: Building a Zero-Slop Developer Content Engine From Git History
published: true
tags: python, architecture, git, security
canonical_url: https://basfore.dev/blog/building-zero-slop-developer-content-engine
---

Every week, developers solve real engineering problems. We debug race conditions in distributed job queues, swap out heavy dependencies for lightweight standard library primitives, and rewrite database queries to take response times from 400 milliseconds down to 12 milliseconds.

Yet when you open developer social feeds, almost none of this work is visible. 

When developers try to automate technical writing with standard AI tools, the results are painful to read. Generic models generate paragraphs full of empty corporate phrasing. They write that your minor bug fix "serves as a testament to ongoing innovation in a rapidly evolving technological landscape." They invent metrics you never measured. They overuse em-dashes to connect disjointed thoughts.

We built Lore to solve this problem. Lore is an open-source, local-first CLI that mines your local git repositories, extracts semantic changes using abstract syntax tree (AST) inspection, scrubs credentials through an entropy-based data loss prevention (DLP) scanner, and runs draft copy through a 3-pass anti-slop engine.

Here is the engineering architecture behind building a zero-slop developer content engine.

---

## The Core Technical Problems

Turning git history into technical writing requires solving four separate systems challenges:

1. **The Context Saturation Problem:** Raw `git diff` output is dominated by lockfiles, minified bundles, and generated code. Feeding 2,000 lines of raw diff text into an LLM exhausts prompt context while obscuring the actual architectural change.
2. **The Secret Leakage Problem:** Development diffs contain environment keys, testing tokens, database URIs, and internal network hostnames. Sending unscrubbed diffs to external APIs creates an immediate security breach.
3. **The Clean Commit Fallacy:** Real development branches contain messy commit messages like `wip`, `temp`, `checkpoint`, and `fix typo`. An automated tool that summarizes commits literally will produce useless updates.
4. **The Machine Voice Problem:** Default LLM prose uses repetitive grammatical structures: copula avoidance ("serves as", "stands as"), negative parallelism ("it is not just X, it is Y"), decorative emojis, and an obsessive reliance on em-dashes.

---

## Architecture Overview

Lore operates entirely as a local pipeline. By default, it runs against local Ollama models (`gemma4:e2b`, `qwen3:4b`, `llama3.2:3b`), requiring zero network egress and zero cloud API keys.

```
[Local Git Repo]
       │
       ▼
[Git Scanner & Time-Clustering]
       │
       ▼
[Local DLP & Entropy Engine] ──► [Redacted Diffs]
       │
       ▼
[AST Semantic Extractor]     ──► [Function & Class Deltas]
       │
       ▼
[Atom Evidence Ledger]       ──► [Deterministic Claims + SHAs]
       │
       ▼
[Multi-Model Router]         ──► [Raw First Draft]
       │
       ▼
[3-Pass Anti-Slop Engine]    ──► [Humanized Engineering Prose]
       │
       ├─────────────────────────┬─────────────────────────┐
       ▼                         ▼                         ▼
[Visual Diff Engine]     [Local Web Dashboard]     [Stdio MCP Server]
(1200x675 SVG / PNG)     (127.0.0.1:4748)          (Claude / Cursor)
```

---

## Step 1: Pre-Prompt DLP and Shannon Entropy Scanning

You cannot trust an LLM prompt to ignore sensitive data. Negative prompting ("Do not output API keys") fails regularly because generative models attend to all input tokens during decoding.

Lore runs a deterministic security scanner before any text enters prompt synthesis.

First, lines exceeding 2,048 characters are dropped to prevent regular expression denial of service (ReDoS). Second, the scanner applies 42 Gitleaks-derived regular expressions that detect known credential structures, including AWS keys, GitHub personal access tokens, and private PEM certificate blocks.

Third, to catch unformatted high-entropy secrets like custom database passwords, Lore evaluates Shannon entropy across all tokens with a length of 24 characters or more:

```python
import math
from collections import Counter

def shannon_entropy(token: str) -> float:
    if not token:
        return 0.0
    length = len(token)
    counts = Counter(token)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in counts.values()
    )
```

We configure different entropy thresholds depending on character sets:
* Base16 hexadecimal strings: Entropy >= 3.75 triggers a secret flag.
* Base64 and ASCII alphanumeric strings: Entropy >= 4.8 triggers a secret flag.
* Sensitive variable identifiers (names matching `password`, `token`, `secret`, `api_key`): Threshold drops to length >= 10 and entropy >= 3.2.

To prevent false alarms on 40-character git commit hashes, any candidate hexadecimal token is checked against the local git object database. If the hash exists in the repository history, Lore whitelists it as a legitimate commit SHA.

---

## Step 2: AST Diffing Over Raw Numstat

Feeding raw unified diffs into a language model is inefficient. A 500-line diff usually contains only 20 lines of genuine architectural intent.

Lore parses Python files into abstract syntax trees using Python's standard library `ast` module. For TypeScript, Go, and Rust, it extracts declaration tokens.

When an engineer alters a worker process, rather than passing every modified line of formatting, the AST extractor identifies:
* Modified function signatures and default parameter additions.
* New exception types caught in `try/except` blocks.
* Added assertions and test expectations.
* Database schema modifications.

For example, when scanning a background queue refactor, the extractor outputs this structural summary:

```json
{
  "file": "worker/queue.py",
  "modified_functions": ["process_batch"],
  "signature_change": "added max_retries: int = 3",
  "exceptions_handled": ["ConnectionResetError"],
  "assertions_added": ["assert batch.is_valid()"],
  "lines_added": 14,
  "lines_deleted": 4
}
```

This transforms a 120-line diff into 35 tokens of structured context. The model receives exact functional facts instead of guessing intent from line fragments.

To handle dirty trees and messy development branches, Lore clusters commits within 4-hour temporal windows. It ignores low-entropy commit messages like `wip` or `checkpoint`, evaluating the consolidated AST diff across the entire cluster.

---

## Step 3: The 3-Pass Anti-Slop Humanization Engine

Generating a draft from structured data is only half the problem. Raw LLM outputs contain consistent stylistic patterns that technical readers find unreadable.

Lore runs all generated text through a deterministic 3-pass cleanup pipeline:

### Pass 1: Pattern and Vocabulary Cleansing
This pass runs regex replacements in under 1 millisecond. It executes five specific cleanups:
1. Strips conversational chatbot prefixes ("Here is your draft:", "Sure thing!", "Without further ado").
2. Replaces curly quotes with standard straight quotes (`"` and `'`).
3. Replaces all em-dashes with commas or periods. The em-dash is a frequent AI marker that models use to avoid structuring compound sentences.
4. Corrects copula avoidance. Models avoid simple verbs like "is" or "has", preferring elaborate replacements. Lore maps "serves as a" to "is a", "stands as" to "is", and "boasts a" to "has a".
5. Strips negative parallelism ("It is not just about speed, it is about reliability" becomes "Reliability matters").

### Pass 2: Rhythm Variation and Header Cleanup
Pass 2 inspects paragraph structure. It removes inline headers that simply restate the following line (such as `**Performance:** Performance improved`). It strips promotional adjectives like "groundbreaking", "pivotal", and "testament".

### Pass 3: Adversarial Self-Audit
The final pass scans for 35 prohibited AI vocabulary terms, including "delve", "tapestry", "landscape", "foster", "underscore", "utilize", and "leverage". If any term remains, it is removed or substituted with a plain English equivalent.

---

## Step 4: Headless Visual Diff Cards

Technical posts perform significantly better when accompanied by readable code diffs. However, taking manual screenshots from a code editor is tedious, and syntax themes often lack sufficient contrast for mobile feeds.

Lore includes a headless visual diff engine (`lore.visual`) that renders publication-ready diff cards in SVG and PNG formats at 1200x675 (16:9) or 1080x1080 (1:1).

The layout engine enforces strict rules:
* Maximum line width of 84 columns. Any line exceeding 84 characters is truncated with an ellipsis rather than hard-wrapped, preventing ugly line breaks on mobile screens.
* Maximum display of 14 lines for 16:9 cards or 20 lines for 1:1 cards.
* Unchanged lines are collapsed automatically using `// ... unchanged` markers.
* Themes (Tokyo Night, Catppuccin Mocha, One Dark) are calibrated for WCAG AA contrast ratio (> 4.5:1).

The rendering pipeline checks for the `freeze` CLI, falls back to `resvg-py`, and defaults to standalone SVG if no native rasterizer is installed.

---

## Step 5: The Review Workflow and Local Dashboard

Automated content generation should never auto-publish without human review.

Lore provides two review interfaces:
1. An interactive terminal TUI (`lore review`) with keyboard navigation.
2. A zero-dependency local web dashboard running on `127.0.0.1:4748` using Python's built-in `ThreadingHTTPServer`.

The web dashboard opens with an ephemeral CSRF token. It displays all drafted content atoms, their backing git commit evidence, and any anti-slop filters that fired during cleanup.

Engineers can navigate using keyboard shortcuts (J and K for navigation, A for approve, R for reject, E for slide-over editing). The slide-over Markdown editor includes debounced auto-saving, avoiding terminal editor crashes.

---

## Step 6: Model Context Protocol (MCP) Integration

For teams using agent-driven IDEs like Claude Desktop or Cursor, Lore runs a native Model Context Protocol (MCP) server over stdio JSON-RPC 2.0:

```bash
lore mcp
```

This exposes five tools directly to your coding assistant:
* `lore_scan`: Scans recent commits in the current repository.
* `lore_list_atoms`: Lists extracted content atoms and their evidence scores.
* `lore_draft`: Generates a humanized draft for Twitter, LinkedIn, or Dev.to.
* `lore_render_card`: Generates an SVG or PNG code diff card.
* `lore_approve`: Approves a draft for export.

---

## Real-World Dogfooding

We tested Lore against three active repositories:
1. **Lore itself (`projects/lore`):** Python 3.12, Click, Rich, Pydantic, and SQLite. Used to document its own migration from v0.1 to v2.0.
2. **Veltr (`projects/veltr`):** A single-owner personal operating system built with FastAPI, Next.js, and PostgreSQL. Used to generate security engineering breakdowns of Argon2id auth and AES-GCM credential encryption.
3. **Ilvuno (`projects/ilvuno`):** A minimalist Go CLI for verifying multi-agent code changes. Used to draft architectural notes on running verification pipelines with zero telemetry.

Across 150 scanned commits, the AST extractor filtered out 82% of irrelevant file modifications, while the DLP engine flagged and redacted 14 test credentials before prompt construction.

---

## Conclusion

Automating developer content does not mean letting a language model invent buzzwords about your codebase. 

By treating the problem as a deterministic pipeline grounded in git commits, AST structures, and strict anti-slop rules, you can produce authentic technical writing in seconds without leaving your terminal.

Lore is open source under the MIT license. You can install it locally and test it against your own git history:

```bash
pip install -e .
lore init
lore project add .
lore scan
lore generate --platform thread
```
