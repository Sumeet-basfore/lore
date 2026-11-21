# CONTEXT.md — Strategic & Business Context for Lore

---

> **Accuracy note (2026-11-21):** The historical roadmap, research estimates, and earlier launch copy below include unverified hypotheses and planned capabilities. For current beta behavior and privacy boundaries, use [`README.md`](./README.md) and [`BETA.md`](./BETA.md). Do not use the older claims as public product guarantees.

## 1. The Product Hypothesis

Lore explores whether developers who want to share engineering work can save time by starting from local Git history instead of manually assembling repository context. The beta is intended to test that workflow with developers who can report where the summaries, evidence, or review process fail.

This is a product hypothesis, not a measured market finding. The research notes do not document a completed interview study or representative survey.

## 2. Current Beta Product Boundary

| Area | Current behavior |
|---|---|
| Git input | The CLI reads commit subjects, timestamps, changed paths, and insertion/deletion counts. It does not include source diffs in the scan-to-draft prompt. |
| Evidence | Drafts can be traced to commit SHAs and metadata. Evidence does not verify every generated sentence or prove impact. |
| Models | Ollama at localhost is the default. OpenAI, Anthropic, OpenRouter, Gemini, and another Ollama URL can be configured; those endpoints receive prompt data. |
| Secret checks | Some secret-like file names are skipped. The separate DLP scanner is not connected to scan-to-draft and is not a security boundary. |
| Review | Drafts are stored locally and can be inspected, edited, approved, rejected, and exported. The CLI does not currently expose publishing. |
| Voice | Writing samples are stored locally. Lore derives brief style guidance from sample analysis for prompts; it does not insert the full sample text into the generation prompt. |

Lore provides commit-linked context and deterministic text cleanup. It does not guarantee factual accuracy, complete secret detection, human-sounding prose, or privacy when a remote model endpoint is selected.

## 3. Draft Formats and Narrative Suggestions

The prompt templates suggest structures for several formats. These are starting points for review, not validated storytelling formulas:

### Formula A: The War Story (Bug Fix / Post-Mortem)
1. **Hook:** The unexpected breakdown (e.g. *"Our Redis cache memory spiked to 98% at 3 AM."*)
2. **Investigation:** The false lead and what the logs actually showed.
3. **The Fix:** The exact commit and 4 lines of code that resolved it.
4. **Takeaway:** The concrete engineering rule learned.

### Formula B: The Architectural Decision (Refactor / Stack Decision)
1. **Hook:** Contrarian technical stance (e.g. *"We replaced our microservice pipeline with a single SQLite file."*)
2. **Context:** Why the conventional solution failed our specific scale.
3. **Implementation:** What we built, how long it took, and what changed.
4. **Result:** Include only a result the author can verify; diff counts are not performance metrics.

### Formula C: The Feature Ship (Launch / Build in Public)
1. **Hook:** The concrete capability unlocked for users.
2. **The Problem:** Why existing workflows were clunky.
3. **How it Works:** Crisp breakdown of the workflow.
4. **Next Step / CTA:** Try it out or check the repo.

---

## 4. Monetization Hypotheses

The following ideas are unvalidated planning hypotheses. There is no confirmed pricing, willingness-to-pay evidence, or validated return-on-investment estimate:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Phase 1     │       │     Phase 2     │       │     Phase 3     │       │     Phase 4     │
│   Free OSS CLI  │  ──►  │    Lore Pro     │  ──►  │   Lore Cloud    │  ──►  │ Lore Enterprise │
│  ($0 / forever) │       │   ($12/month)   │       │   ($49/month)   │       │  ($299+/month)  │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
 • Core CLI               • Multi-platform API      • Web Dashboard / Kanban  • Org-wide DevRel
 • Git scanning           • 1-Click Publishing      • GitHub App webhooks     • Multi-seat licenses
 • Ollama + API keys      • Auto-scheduling         • Team voice matching     • IP/Security checks
 • 3-Pass Humanizer       • Analytics & feedback    • Hosted fast LLMs        • Custom integrations
```

### Questions to validate before pricing
* Does the scan-to-draft workflow save enough time to be useful?
* Which parts of the workflow do beta users trust, edit, or reject?
* Would users pay for any capability beyond the local CLI, and what would they expect it to include?

---

## 5. Technology Stack Rationale

* **Python 3.12+ / 3.14:** Universal across developer environments, exceptional ecosystem for text parsing, git bindings, and local/remote LLM interactions.
* **Click + Rich:** Provides a responsive, ergonomic, and aesthetic CLI experience that feels like modern tools (e.g. `uv`, `gh`, `docker`).
* **SQLite:** Local persistence with no separate database service. Lore does not encrypt its database or configuration files.
* **Ollama default:** Lore defaults to an Ollama endpoint at `http://localhost:11434`; other endpoints and remote providers can be configured.
* **Direct HTTP:** The router has direct HTTP adapters for the providers listed in the configuration and README. The project does not use LiteLLM.

---

## 6. Historical Architecture Roadmap (Phases 0 through 9)

This older roadmap records proposed or previously reported architecture work. It is not a current status report, and the presence of a module or test does not mean the normal CLI workflow uses it. Current beta scope and data handling are defined in Section 2 and `BETA.md`.

### Phase 0: Database migration engine and schema evolution
* **Component:** `lore.core.migrations`, `lore.core.database`
* **Schema versioning:** SQLite `PRAGMA user_version` tracking migrations sequentially from v1 to v2.
* **Evolution:** Adds tables and columns for DLP audits, AST diff digests, visual card references, publishing schedules, and MCP session tokens.
* **Verification:** Forward and rollback migrations tested against existing `lore.db` instances with zero data loss. Verified in Commit `e111c43`.

### Phase 1: Local-first DLP scanner and git security sandbox
* **Component:** `lore.scanner.dlp`, `lore.scanner.filters`
* **Data protection:** Pre-scan and pre-generation regex checks combined with Shannon entropy thresholding (entropy >= 4.8 on Base64/ASCII strings of length >= 24, entropy >= 3.75 on Base16 hex strings) to catch API keys, private certificates, JWTs, AWS access keys, and internal connection strings.
* **Sandbox boundaries:** Absolute path traversal prevention, git credential isolation, and strict redaction of sensitive diff lines before prompt templating.
* **Verification:** Verified in Commit `5b9fd25` (34/34 tests passing).

### Phase 2: AST-aware semantic diff and architecture extractor
* **Component:** `lore.extraction.ast_diff`, `lore.extraction.atom_extractor`
* **Semantic parsing:** Analyzes syntax trees (Python `ast`, language regex grammars for Go, Rust, TypeScript) to identify exact functional boundaries: added functions, modified class signatures, deleted methods, and package imports.
* **Token efficiency:** Compresses raw 1,000-line diffs down to high-signal 40-token semantic summaries, avoiding LLM context saturation and prompt truncation.
* **Verification:** Verified in Commit `5ebcda3` (27/27 tests passing) and Commit `5b9fd25` (34/34 tests passing).

### Phase 3: Multi-model router and offline fallback
* **Component:** `lore.generation.router`, `lore.generation.humanizer`
* **Local-first priority:** Native Ollama client targeting local models (`gemma4:e2b`, `qwen3:4b`, `llama3.2:3b`).
* **Cloud fallback:** Optional direct HTTP adapters for Anthropic Claude 3.5 Sonnet, OpenAI GPT-4o, Google Gemini 1.5 Pro, and OpenRouter with timeout budgets.
* **Mock engine:** Deterministic offline mock mode (`LORE_MOCK_LLM=1`) for hermetic CI and test suites.
* **Current verification:** Provider errors stop generation. The test-only mock mode is explicit; there is no automatic fallback to canned text.

### Phase 4: Visual diff card engine
* **Component:** `lore.visual.card_generator`, `lore.visual.layout_engine`, `lore.visual.themes`
* **CLI command:** `lore card [-d diff_file] [-o output.png] [--theme tokyo_night|catppuccin_mocha|one_dark] [--aspect-ratio 16:9|1:1]`
* **Headless rendering:** Produces publication-ready syntax-highlighted code diff cards in SVG and PNG formats with macOS window header, traffic lights, and `lore.dev/diff` badge.
* **Strict layout constraints:** Hard limit of 84 columns with ellipsis truncation, maximum 14 lines for 16:9 aspect ratio (1200x675) or 20 lines for 1:1 aspect ratio (1080x1080), auto-collapsing unchanged context with `// ... unchanged` markers.
* **Themes and accessibility:** Tokyo Night, Catppuccin Mocha, and One Dark themes tuned for WCAG AA contrast ratio (> 4.5:1).
* **Multi-tier rasterizer:** Tries `freeze` CLI, falls back to `resvg-py`, and defaults to pure standalone SVG.

### Phase 5: Approval gateway and web review dashboard
* **Component:** `lore.approval.local_web`, `lore.approval.gateways`, `lore.cli`
* **CLI commands:**
  * `lore review`: Interactive terminal TUI with hotkeys (`[a]` Approve, `[r]` Reject, `[e]` Edit, `[n]` Next, `[p]` Previous, `[w]` Launch Web Dashboard, `[q]` Quit).
  * `lore review --web [--port 4748]`: Launches zero-dependency local web dashboard on `127.0.0.1:4748` (with fallback ports 4749..4755) and opens browser.
* **Security:** Ephemeral CSRF tokens required for every mutation; requests bound strictly to loopback interface.
* **UI ergonomics:** High-density monospace dark UI (`#090D13`). Hotkeys for keyboard navigation (J/K next/prev, A approve, R reject, E edit, C copy).
* **In-browser editor:** Slide-over Markdown editor with debounced 500ms auto-save to `/api/drafts/<id>/update`, eliminating terminal editor TTY crash risks.
* **Live preview:** Inline visual diff cards displayed alongside the Evidence Ledger.
* **External gateways:** Optional outbound webhooks for Slack Block Kit, Discord embeds, and Telegram inline keyboards.

### Phase 6: Multi-platform publishing and scheduling engine
* **Component:** `lore.publishing.scheduler`, `lore.publishing.exporter`, `lore.publishing.social_router`
* **Publishing calendar:** Queue management for queued, approved, and published drafts with optimal posting windows.
* **Platform formatters:** Custom pure `httpx` adapters (zero vendor SDKs):
  * LinkedIn Restli v2 (`/rest/posts`) with unicode monospace formatting. Token refresh is not implemented.
  * Bluesky AT Protocol (`com.atproto.repo.createRecord`) with exact UTF-8 byte offset facets.
  * Twitter Bridge via Web Intent URL and automated PNG clipboard copying (`xclip`/`wl-copy`/`pbcopy`).
  * GitHub Releases generator with formatted features, bug fixes, and commit links.
* **Current limitation:** The publisher modules are not exposed as a `lore` CLI command. The CLI beta flow ends at review and export.

### Phase 7: Model Context Protocol (MCP) server
* **Component:** `lore.mcp.server`
* **CLI command:** `lore mcp` (stdio JSON-RPC 2.0 server).
* **Exposed tools:** `lore_scan`, `lore_list_atoms`, `lore_draft`, `lore_render_card`, `lore_approve`.
* **Client integration:** Auto-registers in Claude Desktop (`claude_desktop_config.json`) and Cursor (`.cursor/mcp.json`).
* **Verification:** Verified in Commit `d86c9be` (10/10 MCP & CLI tests passing).

### Phase 8: Multi-platform launch collateral & dogfooding
* **Component:** `projects/lore/content/`
* **Current content drafts:** `content/launch_twitter_thread.md`, `content/linkedin_architecture_breakdown.md`, `content/devto_technical_article.md`, and `content/github_release_v2.md` describe the current implementation and are not published or release-approved.
* **Historical note:** Earlier versions of these drafts contained unsupported capabilities and metrics; they should not be reused from older Git revisions.

### Phase 9: Senior code quality & security hardening audit
* **Auditors:** Senior Principal Software Engineer, Staff Security Engineer, Senior Release Lead.
* **Security & reliability hardening:**
  * Path traversal sandboxing on `/api/drafts/<id>/card` ensuring image access is contained strictly within authorized directories (`403 Forbidden` on directory escapes).
  * AppleScript quote and backslash escaping in `twitter_bridge.py` preventing OS command injection via malicious image filenames.
  * Sliding window chunking (1,024-char windows with 128-char overlap) in `dlp_scanner.py` and `entropy.py`, eliminating blind spots for padded or minified secrets on lines > 2,048 chars.
  * Legitimate Git commit SHA whitelisting supporting both 40-char SHA-1 and 64-char SHA-256 hashes, preventing valid Evidence Ledger commits from being dropped as secrets.
  * SQLite connection descriptor leak elimination via `@contextmanager` with `finally: conn.close()` and `PRAGMA busy_timeout = 5000`.
  * Nested loop AST masking fix inserting valid `pass` statements to maintain valid Python syntax trees.
  * SSRF prevention in Slack/Discord gateways via strict URL domain allowlisting.
  * HTML entity escaping in Telegram gateway via `html.escape()`.
  * Timing-safe CSRF token comparison via `hmac.compare_digest`.
* **Verification:** Verified in Commit `dd4f5c2` (59/59 tests passing across all 14 test modules).

---

## 7. Current CLI Data Flow

```text
Repository
  ├─ project add: inspect README, package.json, pyproject.toml, and paths for local metadata
  └─ scan: git log metadata + numstat
       ↓
Content atoms: commit subjects, dates, SHAs, changed paths, and line counts
       ↓
Prompt template: project name, atom/evidence fields, tech stack, angle, style guidance
       ↓
Configured Ollama endpoint (localhost by default) or selected remote model provider
       ↓
Deterministic humanizer → local draft database → human review → Markdown/JSON export
```

The scan-to-draft path does not pass source diffs to the model. The standalone DLP scanner and AST inspection code are not wired into this normal CLI path. The CLI does not currently expose publishing, although publisher modules exist separately.

## 8. Verification Record

Beta-readiness verification is recorded in Section 11 and [`BETA_READINESS_PLAN.md`](./BETA_READINESS_PLAN.md). Historical test counts and coverage targets below this section were not measured as current coverage and should not be used as release claims.

## 9. Market and Dogfooding Evidence

Older competitor notes, market estimates, example quotes, and repository case studies are research hypotheses or internal examples. They are not customer interviews, paid user evidence, or independently verified case studies. Validate them before using them in public marketing or pricing decisions.

## 10. Repository and Release State

* **Public repository:** `https://github.com/Sumeet-basfore/lore`
* **Package name in source metadata:** `lore-dev-content`; no package release is published.
* **License:** MIT, tracked in `LICENSE`.
* **Current beta branch:** `beta/lore-readiness`.
* **Release boundary:** The package, GitHub release/tag, and beta announcement remain unpublished unless separately approved.
* **Current install route:** Clone the repository and install from source as documented in `README.md` and `BETA.md`.

---

## 11. Beta Readiness Work (Approved and Implemented)

* **Goal:** Prepare a small developer beta around the CLI workflow: scan a repository, extract evidence-backed atoms, generate a draft, review it, then export it locally.
* **Plan:** [`BETA_READINESS_PLAN.md`](./BETA_READINESS_PLAN.md) records the proposed work, files, acceptance checks, and boundaries.
* **Current status:** Owner approved implementation on branch `beta/lore-readiness` on 2026-11-21. Branch push, pull request, sub-agent review, merge, and push of the merged code are approved.
* **Remaining readiness work:** No code work remains within the approved scope. Run an invitation-based beta using the source install guide and collect tester feedback. Package publication, a GitHub release/tag, and a public beta announcement remain separately approved actions.
* **Release boundary:** Do not publish a package, create a GitHub release or tag, or post a public beta announcement without separate approval.
* **Slice 1 complete (`3a57f51`, review fixes `f7cd7d7` and `697315d`):** Publication results distinguish provider-confirmed posts, Twitter compose hand-offs, explicit simulations, and failures. Publishing requires an approved draft; missing credentials and validation/client errors do not queue retries. HTTP 408/429 and 5xx errors remain retryable; `Retry-After` supports seconds and HTTP dates, never shortens the provider delay, and falls back to 60 seconds for missing, malformed, or over-one-year values. Focused publisher tests pass (27 tests).
* **Slice 2 complete (`4f0adad`):** The distribution is now `lore-dev-content`; the `lore` command remains unchanged. Added the MIT license, set the minimum Python version to 3.12, aligned classifiers, and included Jinja templates in built artifacts. Wheel and source archive builds passed; a fresh Python 3.14 virtual environment installed the wheel and ran `lore --help`. PyPI availability was checked on 2026-11-21; the package was not published.
* **Slice 3 complete (`9aa3875`):** README, beta guide, context, and four launch/release drafts now match the CLI workflow and state its privacy limits. Config output redacts sensitive values, onboarding asks for a provider-specific remote model, and ordinary provider errors stop generation instead of triggering canned text. The explicit `LORE_MOCK_LLM=1` test mode is documented. Focused publisher, CLI, and MCP checks passed (30 tests).
* **Slice 4 verification:** Full suite passes after both review rounds (86 tests); compileall and `git diff --check` pass. Wheel and source archive builds passed with SPDX `MIT` metadata, `setuptools>=77`, and no setuptools deprecation warning. Both artifacts include the license and prompt templates. A fresh Python 3.14 virtual environment installed the wheel and completed project add, scan, generate, inspect, approve, and export. The resulting wheel ran `lore --help`.
* **PR:** [#1 — Prepare Lore for a small beta](https://github.com/Sumeet-basfore/lore/pull/1) merged to `main` in merge commit `571ecad`. The requested independent reviewer confirmed all findings were resolved at `697315d` and found no remaining retry-path issues. No GitHub CI workflow is configured; local full-suite, package, and clean-install checks passed.
* **Current status:** Local `main` is synchronized with `origin/main`. The source install route and tester guidance are ready for a small invited beta. No package, GitHub release/tag, or public announcement has been created.
* **Next step:** Invite a small group of testers, gather feedback through GitHub issues, and use that feedback to decide whether a public release is warranted.
* **README polish (`docs/readme-polish`):** Added quick navigation, linked the beta guide, separated macOS/Linux and Windows installation steps, organized the first run into scan, draft/review, and export stages, documented the PowerShell editor setting, and made Windows setup work with newer Python 3 versions without requiring environment activation.
* **Logo prototypes (`design/logo-prototypes`):** Added three restrained, self-contained SVG logo prototypes under `assets/logo-prototypes/` exploring Git commit lineage, editorial proofreading craft, and diff evidence strata.
* **Logo adoption (`brand/evidence-strata-rollout`):** The user selected Evidence Strata as Lore's final logo. The canonical SVG is packaged for the local review dashboard and displayed in the GitHub README; it remains a local vector source for future raster exports.
* **Brand guidelines (2026-11-21):** The user approved the clear-workbench direction and skipped the preview. `DESIGN.md` records the Evidence Strata logo rules, marketing and dashboard tokens, type system, and factual copy boundaries. The landing page remains future work; selected font files are not bundled yet. PR [#3](https://github.com/Sumeet-basfore/lore/pull/3) was merged into `main`. Validation passed: 86 tests, wheel packaging, authenticated dashboard logo delivery, and rejection of an invalid logo token.
* **Terminal workflow implementation (`feat/cwd-aware-terminal-workflow`):** The approved plan is in `TERMINAL_WORKFLOW_PLAN.md`. Slice 1 (`a0cd570`) adds Git-root detection from nested directories/worktrees and normalized project-path lookup. Slice 2 (`177b7b1`) adds current-repository defaults, first-use confirmation, project-safe generation, terminal review/export filters, and a compact Rich terminal presentation. README and beta guide now document a pipx Git-source install and `--force` refresh. The full suite passes (107 tests); isolated Linux pipx install/refresh and commands from outside the checkout passed. Windows and macOS were not exercised here.
* **Draft SVG image work (`feat/draft-svg-illustrations`):** Started from the merged `main` baseline. Commit `b8dbb46` makes PNG conversion explicit: output is structurally validated and fails with an actionable message when no renderer is installed, while preserving the SVG source. Commit `fbc0e37` adds a bounded Pydantic scene schema and self-contained editorial SVG renderer. The CLI adds `lore image generate <draft-id>`, default project `lore-media/` output, editable SVG, optional PNG plus SVG source, safe dashboard preview attachment, overwrite and symlink protection, and `lore draft show` image path output. README, beta guide, and design guidance document the workflow and image-prompt privacy boundary. Focused visual and CLI checks pass (22 tests); full-suite verification follows.


