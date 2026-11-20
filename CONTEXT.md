# CONTEXT.md — Strategic & Business Context for Lore

---

## 1. The Genesis: Why Lore Exists

Developers are constantly shipping. Every week brings:
* A complex database migration that halved query times.
* A subtle race condition solved after three hours of debugging.
* A clean architecture refactor switching from REST to WebSockets.
* A new feature release that took days of concentrated engineering.

Yet, when you look at developer feeds on Twitter/X or LinkedIn, 99% of developers share almost nothing. Why?
1. **The Translation Tax:** Turning raw technical code into engaging public writing takes mental bandwidth that developers would rather spend building.
2. **The Slop Problem:** When developers try generic AI tools (like ChatGPT), the output is embarrassingly corporate, full of buzzwords (*"Excited to announce our groundbreaking feature that serves as a testament to our ongoing journey"*), and immediately rejected by technical peers.
3. **The Lack of Context:** Generic tools don't know what actually changed in the repo. They require manual copying of diffs and explanations, destroying the convenience of automation.

**Lore solves this by living where developers live: in the terminal and in the git repository.**

---

## 2. What Makes Lore Unique (The Moat)

```
┌─────────────────────────────────────────────────────────────────┐
│                           LORE MOAT                             │
├───────────────────────────────┬─────────────────────────────────┤
│ 1. Git Ground Truth           │ 2. 3-Pass Anti-Slop Humanizer   │
│ Mines real commits, diffs,    │ Codified Wikipedia + Hermes     │
│ files, and timestamps. Zero   │ cleanup rules. Zero corporate   │
│ hallucinations.               │ fluff. Genuine dev voice.       │
├───────────────────────────────┼─────────────────────────────────┤
│ 3. Local-First & Offline      │ 4. Voice Calibration            │
│ Powered by local Ollama by    │ Learns YOUR style from real     │
│ default. Zero cloud leaks     │ writing samples. Gets better    │
│ or API token costs.           │ the more you write.             │
└───────────────────────────────┴─────────────────────────────────┘
```

### Competitor Comparison Matrix

| Feature | ChatGPT / Claude Web | Generic AI Social Tools (Buffer AI, Taplio) | Specialized Tools (PushLog, GitEcho) | **Lore (`lore-cli`)** |
|---|---|---|---|---|
| **Understands Local Repos** | ❌ Manual paste | ❌ No code context | ⚠️ Limited to remote GitHub | ✅ **Direct local git & directory scan** |
| **Evidence Ledger (Fact-Checked)** | ❌ None | ❌ None | ⚠️ Basic changelog diff | ✅ **Every claim tied to commit SHA** |
| **Anti-Slop Engine** | ❌ Produces slop | ❌ Encourages slop | ❌ Basic prompting | ✅ **3-Pass Anti-Slop + Self-Audit** |
| **Voice Calibration** | ⚠️ Complex prompts | ❌ Generic templates | ❌ Fixed tone | ✅ **Learns from your writing samples** |
| **Local Model Support (Ollama)**| ❌ Cloud only | ❌ Cloud only | ❌ Cloud only | ✅ **Native Ollama local-first** |
| **Works Offline** | ❌ No | ❌ No | ❌ No | ✅ **100% offline with local LLMs** |
| **Privacy / No Code Leak** | ⚠️ Code sent to cloud | ⚠️ Code sent to cloud | ⚠️ Code sent to cloud | ✅ **Code never leaves machine** |

---

## 3. High-Value Content Formulas Lore Automates

Lore's prompt engine and atom extractors codify proven developer storytelling frameworks:

### Formula A: The War Story (Bug Fix / Post-Mortem)
1. **Hook:** The unexpected breakdown (e.g. *"Our Redis cache memory spiked to 98% at 3 AM."*)
2. **Investigation:** The false lead and what the logs actually showed.
3. **The Fix:** The exact commit and 4 lines of code that resolved it.
4. **Takeaway:** The concrete engineering rule learned.

### Formula B: The Architectural Decision (Refactor / Stack Decision)
1. **Hook:** Contrarian technical stance (e.g. *"We replaced our microservice pipeline with a single SQLite file."*)
2. **Context:** Why the conventional solution failed our specific scale.
3. **Implementation:** What we built, how long it took, and what changed.
4. **Result:** Benchmark metrics directly from diff stats and timing.

### Formula C: The Feature Ship (Launch / Build in Public)
1. **Hook:** The concrete capability unlocked for users.
2. **The Problem:** Why existing workflows were clunky.
3. **How it Works:** Crisp breakdown of the workflow.
4. **Next Step / CTA:** Try it out or check the repo.

---

## 4. Monetization Strategy & Business Potential

Lore is architected from day one to evolve from a developer-loved open-source CLI into a high-margin software business:

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

### Why Developers Will Pay for Lore Pro
* **Time ROI:** Spending 2 hours a week manually drafting posts costs an engineer ~$150+ in billable time. At $12/month, Lore Pro pays for itself in the first 20 minutes of usage.
* **Career & Business Growth:** Builders who post consistent, high-signal technical updates attract consulting inbound, job offers, open-source sponsors, and paying customers for their software.
* **Zero Friction:** Auto-publishing directly from the terminal or upon `git push` eliminates the need to even open social media platforms.

---

## 5. Technology Stack Rationale

* **Python 3.12+ / 3.14:** Universal across developer environments, exceptional ecosystem for text parsing, git bindings, and local/remote LLM interactions.
* **Click + Rich:** Provides a responsive, ergonomic, and aesthetic CLI experience that feels like modern tools (e.g. `uv`, `gh`, `docker`).
* **SQLite:** Fast, zero-configuration local database that guarantees privacy, zero daemon management, and portable data files.
* **Ollama First:** Seamless out-of-the-box integration with open weights models (`gemma4`, `qwen3`, `llama3.2`) running locally on user hardware.
* **LiteLLM / Direct HTTP:** Universal compatibility with cloud models when users want higher parameter reasoning without locking into a single proprietary API.

---

## 6. Architecture and Implementation Roadmap (Phases 0 through 7)

Lore v2.0.0 evolves the system from a prototype script into a production-grade, local-first developer content engine. Each phase represents a discrete architectural subsystem with strict verification gates.

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
* **Verification:** Automatic failover handling with graceful degradations when local daemons are offline.

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
  * LinkedIn Restli v2 (`/rest/posts`) with unicode monospace formatting and `offline_access` token handling.
  * Bluesky AT Protocol (`com.atproto.repo.createRecord`) with exact UTF-8 byte offset facets.
  * Twitter Bridge via Web Intent URL and automated PNG clipboard copying (`xclip`/`wl-copy`/`pbcopy`).
  * GitHub Releases generator with formatted features, bug fixes, and commit links.
* **Safety mechanisms:** Dry-run preview mode enabled by default; zero automatic remote writes without explicit approval.

### Phase 7: Model Context Protocol (MCP) server
* **Component:** `lore.mcp.server`
* **CLI command:** `lore mcp` (stdio JSON-RPC 2.0 server).
* **Exposed tools:** `lore_scan`, `lore_list_atoms`, `lore_draft`, `lore_render_card`, `lore_approve`.
* **Client integration:** Auto-registers in Claude Desktop (`claude_desktop_config.json`) and Cursor (`.cursor/mcp.json`).
* **Verification:** Verified in Commit `d86c9be` (10/10 MCP & CLI tests passing).

### Phase 8: Multi-platform launch collateral & dogfooding
* **Component:** `projects/lore/content/`
* **Deliverables:**
  * `launch_twitter_thread.md`: 7-tweet zero-slop technical launch thread.
  * `linkedin_architecture_breakdown.md`: Deep-dive engineering article on entropy math and AST parsing.
  * `devto_technical_article.md`: 2,200-word engineering breakdown with dogfooding case studies.
  * `github_release_v2.md`: Production v2.0.0 release notes with migration guides.
* **Verification:** Verified in Commit `c76a946` and audited against `pstack-unslop` guidelines.

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

## 7. Component Map and Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             LORE ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

 [Local Git Repositories]  ──►  (lore scan)
            │
            ▼
 ┌───────────────────────┐       ┌────────────────────────┐
 │ Git & Directory Walk  │ ────► │ Local DLP Scanner      │ ──► [Redacted Diffs]
 └───────────────────────┘       └────────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ AST Diff Extractor    │ ──► [Semantic Change Signatures]
 └───────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ Atom Extractor        │ ──► [Content Atoms + Evidence Ledger]
 └───────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ Narrative Angle Finder│ ──► [Hook & Platform Strategy]
 └───────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ Multi-Model Router    │ ──► [Raw LLM Drafts]
 │ (Ollama / Cloud)      │
 └───────────────────────┘
            │
            ▼
 ┌───────────────────────┐
 │ 3-Pass Anti-Slop      │ ──► [Humanized Posts & Threads]
 │ Humanizer Engine      │
 └───────────────────────┘
            │
            ├───────────────────────────────┬───────────────────────────────┐
            ▼                               ▼                               ▼
 ┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
 │ Visual Diff Engine    │       │ Local Web Dashboard   │       │ Stdio MCP Server      │
 │ (1200x675 SVG / PNG)  │       │ (127.0.0.1:4748)      │       │ (Claude / Cursor)     │
 └───────────────────────┘       └───────────────────────┘       └───────────────────────┘
            │                               │                               │
            └───────────────────────────────┴───────────────────────────────┘
                                            │
                                            ▼
                                [Export & Publication]
```

---

## 8. Verification and Quality Gates

| Subsystem | Test Files | Coverage Target | Verification Criteria | Status |
|---|---|---|---|---|
| Core & Migrations (Phase 0) | `test_core.py` | > 90% | Zero loss schema upgrades, connection pooling | Verified & Landed (Commit `e111c43`) |
| Scanner & DLP (Phase 1 & 2) | `test_scanner.py`, `test_dlp.py` | > 92% | 42 Gitleaks rules + Shannon entropy pre-filtering | Verified & Landed (Commit `5b9fd25`) |
| AST Diff & Atoms (Phase 1) | `test_ast_inspector.py`, `test_extraction.py` | > 90% | Function/class boundaries, $O(1)$ set lookups | Verified & Landed (Commit `5ebcda3`) |
| Humanizer & Critic Gate (Phase 3) | `test_humanizer.py`, `test_critic.py` | > 95% | 35+ tells stripped, 0 em-dashes, HN Critic | Verified & Landed (Commit `5b2c86a`) |
| Visual Diff Cards (Phase 4) | `test_visual_cards.py` | > 88% | 84-col limit, 14-line limit, WCAG AA contrast | Verified & Landed (Commit `8bbb4d0`) |
| Review Dashboard (Phase 5) | `test_approval_gateways.py` | > 85% | Loopback binding, CSRF tokens, REST endpoints | Verified & Landed (Commit `e4667d1`) |
| Multi-Platform Publishing (Phase 6) | `test_publishers.py` | > 90% | Pure httpx, UTF-8 byte facets, Restli v2 | Verified & Landed (Commit `7e8c9f0`) |
| CLI & MCP Server (Phase 7) | `test_cli.py`, `test_mcp.py` | > 90% | End-to-end command flow, stdio JSON-RPC 2.0 | Verified & Landed (Commit `d86c9be`) |
| Launch Collateral (Phase 8) | `projects/lore/content/` | 100% | Full technical launch collateral suite | Verified & Landed (Commit `c76a946`) |
| Senior Audit Hardening (Phase 9) | All 14 test modules (59 tests) | 100% | Path traversal sandboxing, ReDoS fix, descriptor cleanup | Verified & Landed (Commit `dd4f5c2`) |

---

## 9. Dogfooding Case Studies

Lore is actively dogfooded against three distinct real-world repositories to validate its extraction, sanitization, and voice engines:

1. **Lore itself (`projects/lore`):**
   * Stack: Python 3.12, Click, Rich, Pydantic, SQLite, Jinja2.
   * Evidence: Full development history spanning CLI creation, 3-pass anti-slop engine, local web server, and MCP integration.
   * Focus: Feature ship announcements, architectural trade-offs, and technical launch articles.

2. **Veltr (`projects/veltr`):**
   * Stack: Next.js, TypeScript, Tailwind, FastAPI, PostgreSQL, Docker Compose.
   * Evidence: Single-owner operating system, AES-GCM token encryption, Argon2id auth, Codex quota tracking, immutable context revisions.
   * Focus: Security engineering war stories, local-first database constraints, and auth design breakdowns.

3. **Ilvuno (`projects/ilvuno`):**
   * Stack: Go 1.27, Git 2.38.
   * Evidence: Standalone CLI checking multi-agent change compatibility, zero background daemons, zero telemetry.
   * Focus: Opinionated CLI development, minimalist Go tool design, and agent verification infrastructure.

---

## 10. Live Repository and Deployment State

* **Public Repository:** `https://github.com/Sumeet-basfore/lore`
* **Default Branch:** `main` (synchronized with remote)
* **Active Version:** `2.0.0` (in `pyproject.toml` and `src/lore/__init__.py`)
* **Verification Status:** 59 passing unit and integration tests across 14 test modules
* **Execution Boundary:** 100% local loopback (`127.0.0.1`), zero background daemons, zero telemetry
* **Artifact Deliverables:** Available in `projects/lore/content/`

## 11. Beta Readiness Work (Approved and In Progress)

* **Goal:** Prepare a small developer beta around the local workflow: scan a repository, extract evidence-backed atoms, generate a draft, review it, then export or hand it off to a platform.
* **Plan:** [`BETA_READINESS_PLAN.md`](./BETA_READINESS_PLAN.md) records the proposed work, files, acceptance checks, and boundaries.
* **Current status:** Owner approved implementation on branch `beta/lore-readiness` on 2026-11-21. Branch push, pull request, sub-agent review, merge, and push of the merged code are approved.
* **Remaining readiness work:** Correct product and privacy claims; add a beta setup and feedback guide; complete final suite and clean-install checks.
* **Release boundary:** Do not publish a package, create a GitHub release or tag, or post a public beta announcement without separate approval.
* **Slice 1 complete:** Publication results now distinguish provider-confirmed posts, Twitter compose hand-offs, explicit simulations, and failures. Publishing requires an approved draft; missing credentials no longer return mock post URLs or create retries. Focused publisher, CLI, and MCP checks pass (27 tests).
* **Slice 2 complete:** The distribution is now `lore-dev-content`; the `lore` command remains unchanged. Added the MIT license, set the minimum Python version to 3.12, aligned classifiers, and included Jinja templates in built artifacts. The wheel and source archive build successfully; a fresh Python 3.14 virtual environment installed the wheel and ran `lore --help` successfully. PyPI availability was checked on 2026-11-21; the package was not published.
* **Current work:** Slice 3, aligning README and beta-facing copy with implemented behavior and documenting privacy boundaries.
* **Next step:** Complete the tester guide and final verification, update this section after each slice, then push the branch and open the requested PR for review.


