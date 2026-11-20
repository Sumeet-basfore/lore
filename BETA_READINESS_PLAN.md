# Lore Beta Readiness Plan

**Status:** Draft for owner review. No implementation changes have started.

## Goal

Prepare Lore for a small, invitation-based beta with developers who can report problems. The beta should let a developer install Lore, scan a local repository, make an evidence-linked draft, review it, and export it without being misled about whether anything was published or how repository data is handled.

This plan does not include a hosted service, billing, enterprise sales, or a public launch. It does not create a GitHub release, tag, or social post. Those require a separate go-ahead after the beta build is ready.

## Current findings

1. `LinkedInPublisher`, `BlueskyPublisher`, and `GitHubReleasePublisher` can return successful mock URLs when credentials are missing or `LORE_MOCK_LLM=1`. `SocialRouter` treats every successful result as a completed publication. `TwitterBridgePublisher` returns a web-intent URL, which opens a compose flow rather than confirming a published post. The existing publisher test currently expects mock success to change a draft to `PUBLISHED`.
2. `pyproject.toml` names the distribution `lore-cli`, which is already used on PyPI by an unrelated codebase tool. The README links to an MIT license, but no `LICENSE` file is tracked. The declared Python minimum is 3.10, while `AGENTS.md` requires Python 3.12 or newer.
3. The README promises zero hallucinations and zero leaks, calls the DLP engine enterprise-grade, and claims LinkedIn token refresh. These claims need to match code and tested behavior. The repository has no release artifacts or public install path through the intended package name.
4. The research folder contains market estimates and persona quotations without source references or a described interview method. Treat those as hypotheses, not beta validation.

## Recommended beta scope

Keep the beta focused on the local workflow already present:

`scan local Git history → extract evidence-backed atoms → generate a draft → human review → export or deliberately hand off to a platform`

Direct publishing remains supported only where Lore receives a confirmed platform response. Missing credentials, mock execution, and compose hand-offs must never be shown as published. The beta does not claim that DLP catches every secret or that generated text cannot contain unsupported statements.

## Work plan

### Slice 1: Make publication outcomes truthful

**Likely files:** `src/lore/publishing/base.py`, `linkedin.py`, `bluesky.py`, `github_release.py`, `twitter_bridge.py`, `social_router.py`, `src/lore/core/models.py`, `tests/test_publishers.py`, and any affected CLI tests.

- Represent actual publication, user hand-off, simulation, and failure as distinct outcomes.
- Treat missing credentials as a visible failure. Do not return example URLs as real posts.
- Keep model mock mode separate from publishing mock mode. A publisher simulation must be clearly marked and must not set a draft to `PUBLISHED`.
- Mark a draft `PUBLISHED` only after an external platform confirms creation. Keep Twitter web-intent drafts approved until the user completes the platform flow and Lore can verify the result; otherwise report the hand-off accurately.
- Review retry queue behavior so credential and validation errors do not create misleading retry loops.
- Add regression coverage for missing credentials, explicit simulation, confirmed API publication, failed API calls, and Twitter hand-off state.

**Acceptance:** No mock or hand-off path writes `PUBLISHED`; every success URL comes from an actual provider response; failures explain the needed action without exposing credentials.

### Slice 2: Make installation and licensing usable

**Likely files:** `pyproject.toml`, new `LICENSE`, README install section, and packaging metadata/tests if needed.

- Select and verify an available distribution name. Keep the user-facing `lore` command if the chosen distribution allows it.
- Add the license file that matches the declared license and README badge.
- Align the Python minimum and classifiers with the repository contract (`>=3.12`) or explicitly resolve that contract mismatch before changing metadata.
- Document and verify one clean beta installation route. Build the wheel and source archive, install in a fresh environment, and confirm the `lore` command starts.

**Acceptance:** A new tester can follow one documented install path; package metadata, license file, README, and supported Python versions agree; the selected distribution name is not already taken.

### Slice 3: Align product claims and privacy details

**Likely files:** `README.md`, `CONTEXT.md`, and launch copy under `content/` if it will be used for the beta.

- Replace absolute guarantees such as “zero hallucinations” and “zero leaks” with precise descriptions of evidence linking, redaction checks, and their limits.
- Correct publisher descriptions: distinguish direct publishing from opening a web compose flow, and remove the token-refresh claim unless the implementation actually refreshes tokens.
- State when local Ollama is used, when configured remote providers receive prompt data, what is stored locally, and what beta features contact a remote service.
- Replace unverified market statistics and invented-looking interview quotes in beta-facing copy with sourced facts or clearly labeled hypotheses. Keep internal research claims separate from product guarantees.
- Add a short beta guide with setup, supported workflow, known limitations, privacy boundaries, and a feedback route.

**Acceptance:** Every beta-facing capability and security statement maps to code or an identified source; the guide tells testers what data remains local and what may be sent to a selected provider.

### Slice 4: Beta verification and hand-off

**Likely files:** targeted tests, optional GitHub issue templates, README, beta guide, and `CONTEXT.md`.

- Run focused publisher and CLI tests while implementing the related slices.
- Run the full existing test suite once after all slices, plus CLI and package-install smoke checks.
- Verify documentation examples against actual command names and options; check the diff for credentials and unsupported claims.
- Record results, known limitations, and the local commit hashes in `CONTEXT.md` after each completed slice.
- Make a separate local commit for each completed feature slice, following `AGENTS.md`.

**Acceptance:** Focused checks and the final suite pass; installation and the documented scan-to-export flow work in a clean environment; known limitations are visible; context and commits match the delivered state.

## Out of scope

- Building a cloud dashboard, subscriptions, analytics, team permissions, or new social APIs.
- Promising enterprise security, complete secret detection, or guaranteed human writing.
- Publishing or announcing the beta on GitHub, Reddit, X, Indie Hackers, or other channels.
- Pushing commits or creating public releases as part of this preparation.

## Review decisions

Please review the beta scope, especially the treatment of social publishing. The recommendation is to preserve direct publishing only when provider confirmation is available and treat the Twitter web intent as a hand-off. If this scope is approved, implementation will begin with Slice 1 and `CONTEXT.md` will be updated after every slice.
