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
