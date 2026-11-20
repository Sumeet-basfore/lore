# Lore Beta Readiness Plan

**Status:** Approved for implementation on branch `beta/lore-readiness` (2026-11-21).

## Goal

Prepare Lore for a small, invitation-based beta with developers who can report problems. The beta should let a developer install Lore, scan a local repository, make an evidence-linked draft, review it, and export it with a clear account of repository data handling.

This plan does not include a hosted service, billing, enterprise sales, or a public launch. The owner has approved pushing the feature branch, opening a pull request, obtaining a sub-agent review, merging, and pushing the merged code. It does not include publishing a package, creating a GitHub release or tag, or posting a beta announcement; those still require separate approval.

## Current findings

1. `LinkedInPublisher`, `BlueskyPublisher`, and `GitHubReleasePublisher` can return successful mock URLs when credentials are missing or `LORE_MOCK_LLM=1`. `SocialRouter` treats every successful result as a completed publication. `TwitterBridgePublisher` returns a web-intent URL, which opens a compose flow rather than confirming a published post. The existing publisher test currently expects mock success to change a draft to `PUBLISHED`. These publishing modules are not exposed as a `lore` CLI command, so publishing is not part of the beta user workflow.
2. The former distribution name `lore-cli` is already used on PyPI by an unrelated codebase tool. The README links to an MIT license, but no `LICENSE` file is tracked. The declared Python minimum is 3.10, while `AGENTS.md` requires Python 3.12 or newer.
3. The README promises zero hallucinations and zero leaks, calls the DLP engine enterprise-grade, and claims LinkedIn token refresh. These claims need to match code and tested behavior. The repository has no release artifacts or public install path through the intended package name.
4. The research folder contains market estimates and persona quotations without source references or a described interview method. Treat those as hypotheses, not beta validation.
5. The normal scan-to-draft path reads git commit metadata and builds atoms from commit subjects, changed paths, and diff counts; it does not read source diff contents. The separate DLP scanner is not connected to this path. `lore config list` and `lore config set api_key ...` currently print the configured API key, and generation silently falls back to canned mock text when the selected model fails.
6. `lore init` asks for a remote provider but reuses the prior model name, which defaults to an Ollama model and is usually invalid for a remote provider.

## Recommended beta scope

Keep the beta focused on the local workflow already present:

`scan local Git history → extract evidence-backed atoms → generate a draft → human review → export`

Publishing modules are not exposed by the beta CLI, so the user workflow ends at local export. In the internal publisher layer, missing credentials, simulations, and compose hand-offs must not be shown as published. The beta does not claim that DLP catches every secret or that generated text cannot contain unsupported statements.

## Work plan

### Slice 1: Make publication outcomes truthful

**Likely files:** `src/lore/publishing/base.py`, `linkedin.py`, `bluesky.py`, `github_release.py`, `twitter_bridge.py`, `social_router.py`, `src/lore/core/models.py`, `tests/test_publishers.py`, and any affected CLI tests.

- Represent actual publication, user hand-off, simulation, and failure as distinct outcomes.
- Treat missing credentials as a visible failure. Do not return example URLs as real posts.
- Keep model mock mode separate from publishing mock mode. A publisher simulation must be clearly marked and must not set a draft to `PUBLISHED`.
- Require `DraftStatus.APPROVED` before dispatching any publication attempt.
- Mark a draft `PUBLISHED` only after an external platform confirms creation. Keep Twitter web-intent drafts approved and report the hand-off accurately; do not claim Lore can verify completion of the external compose flow.
- Review retry queue behavior so credential and validation errors do not create misleading retry loops.
- Add regression coverage for missing credentials, explicit simulation, confirmed API publication, failed API calls, and Twitter hand-off state.

**Acceptance:** Unapproved drafts never reach a publisher; no mock or hand-off path writes `PUBLISHED`; every publication URL comes from an actual provider response; missing-credential failures do not enter the retry queue.

### Slice 2: Make installation and licensing usable

**Likely files:** `pyproject.toml`, new `LICENSE`, README install section, and packaging metadata/tests if needed.

- Select and verify an available distribution name. Keep the user-facing `lore` command if the chosen distribution allows it.
- Add the license file that matches the declared license and README badge.
- Align the Python minimum and classifiers with the repository contract (`>=3.12`) or explicitly resolve that contract mismatch before changing metadata.
- Document and verify one clean beta installation route. Build the wheel and source archive, install in a fresh environment, and confirm the `lore` command starts.

**Acceptance:** A new tester can follow one documented install path; package metadata, license file, README, and supported Python versions agree; the selected distribution name is not already taken.

**Status:** Complete. The distribution is `lore-dev-content` (checked against PyPI on 2026-11-21), while its console command remains `lore`. Added the MIT license and aligned Python metadata at `>=3.12`. Wheel and source archive builds passed; a fresh Python 3.14 virtual environment installed the wheel and `lore --help` ran successfully. Prompt templates are present in both artifacts. The package has not been published.

### Slice 3: Align product claims and privacy details

**Likely files:** `README.md`, `CONTEXT.md`, `BETA.md`, `src/lore/cli.py`, `tests/test_cli.py`, and launch copy under `content/` if it will be used for the beta.

- Replace absolute guarantees such as “zero hallucinations” and “zero leaks” with precise descriptions of evidence linking, redaction checks, and their limits.
- Correct publisher descriptions: distinguish direct publishing from opening a web compose flow, and remove the token-refresh claim unless the implementation actually refreshes tokens.
- State when local Ollama is used, when configured remote providers receive prompt data, what is stored locally, and what beta features contact a remote service.
- Replace unverified market statistics and invented-looking interview quotes in beta-facing copy with sourced facts or clearly labeled hypotheses. Keep internal research claims separate from product guarantees.
- Explain that scan and generation use commit metadata and evidence summaries rather than source diffs; the standalone DLP scanner is not active in this workflow. Describe local persistence, provider prompt contents, and optional remote model traffic.
- Ensure configuration commands never print API keys, and stop generation with an error instead of saving canned mock output when a configured model fails.
- Ask for a model name when onboarding a remote provider rather than reusing the Ollama default.
- Add a short beta guide with setup, supported workflow, known limitations, privacy boundaries, and a feedback route.

**Acceptance:** Every beta-facing capability and security statement maps to code or an identified source; the guide tells testers what data remains local and what may be sent to a selected provider; CLI output does not reveal configured keys; provider failures do not create mock drafts.

**Status:** Complete. The README, beta guide, context, and four launch/release drafts now match the current CLI workflow and label privacy limits. Config output redacts sensitive values, remote-provider onboarding asks for a provider-specific model, and generation stops on provider errors. Focused publisher, CLI, and MCP checks pass (30 tests).

### Slice 4: Beta verification and hand-off

**Likely files:** targeted tests, optional GitHub issue templates, README, beta guide, and `CONTEXT.md`.

- Run focused publisher and CLI tests while implementing the related slices.
- Run the full existing test suite once after all slices, plus CLI and package-install smoke checks.
- Verify documentation examples against actual command names and options; check the diff for credentials and unsupported claims.
- Record results, known limitations, and the local commit hashes in `CONTEXT.md` after each completed slice.
- Make a separate local commit for each completed feature slice, following `AGENTS.md`.

**Acceptance:** Focused checks and the final suite pass; installation and the documented scan-to-export flow work in a clean environment; known limitations are visible; context and commits match the delivered state.

**Verification complete:** Full suite passed (76 tests). Wheel and source archive builds passed without setuptools deprecation warnings; Python `>=3.12`, MIT license metadata, license file, and packaged prompt templates were verified. A fresh Python 3.14 virtual environment installed the wheel and completed the documented scan, generate, inspect, approve, and export path. [PR #1](https://github.com/Sumeet-basfore/lore/pull/1) is open; review and merge are pending.

## Out of scope

- Building a cloud dashboard, subscriptions, analytics, team permissions, or new social APIs.
- Promising enterprise security, complete secret detection, or guaranteed human writing.
- Publishing or announcing the beta on GitHub, Reddit, X, Indie Hackers, or other channels.
- Publishing a package, creating a GitHub release or tag, or posting a beta announcement.

## Review decisions

The owner approved this scope on 2026-11-21. Publishing is excluded from the beta CLI workflow because no publish command is exposed. The owner authorized pushing the feature branch, opening a pull request, obtaining a sub-agent review, fixing findings, merging, and pushing the merged code. Package publication, GitHub releases/tags, and public beta announcements remain out of scope without separate approval.
