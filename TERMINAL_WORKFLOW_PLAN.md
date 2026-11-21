# Current-Project Terminal Workflow Plan

**Status:** Approved for implementation; work is in progress.
**Branch:** `feat/cwd-aware-terminal-workflow`
**Date:** 2026-11-21

## Goal

Make Lore usable as a user-level `lore` command from any project directory. When the user is inside a Git repository, project-scoped commands should select that repository automatically, so the common flow does not require repeating `--project <name>`.

Keep Lore local-first, preserve explicit project selection for multi-repository work, and never send a generation prompt until the user runs a generation command.

## Current behavior

- `pyproject.toml` already defines the `lore` console entry point. The README installs Lore into a project virtual environment; the package is not published on PyPI.
- `lore init` configures user-wide author and model settings under `~/.lore/` (or `LORE_HOME`). It does not select the current repository.
- Users register repositories with `lore project add <path> --name <name>`, then pass `--project` to commands such as `scan` and `generate`.
- The SQLite `projects` table already enforces unique project names and paths. Project resolution currently uses name or ID, not the current directory.
- `lore scan` without `--project` scans every registered project. `lore generate` without `--project` can select an atom from the shared database, so it may use a different repository from the user's current directory.
- The `scan` command checks for `.git` as a directory. Git worktrees use a `.git` file, so current-repository detection should use Git itself instead.
- `lore review` shows pending drafts from every project in its terminal interface; `lore review --web` opens the existing dashboard. `lore export` also works across projects and currently has no project filter.
- The `lore` console entry point already exists, but the README installs it into a checkout's virtual environment. A separate user-level installation path is needed for the command to be available from arbitrary project directories.

## Proposed user experience

Install Lore once for the user account, run global onboarding once, then use it from each repository. Keep the existing clone-and-virtual-environment route for contributors and validate `pipx` installing the GitHub source before documenting it as the recommended beta-user path.

```text
# One-time user setup
lore init

# From any directory inside an app repository
lore scan --since "14 days ago"
lore atoms
lore generate --platform linkedin
lore drafts
lore review
lore export --status approved --output-dir ./exports
```

On the first project-scoped command in an unregistered repository, Lore should identify the Git root and ask before registering it. A non-interactive invocation should not prompt or write to the project registry; it should say to run `lore project add .` from the detected Git root (and print the root path if the current directory is nested). `lore project add .` remains available as the explicit path.

Running `lore` with no subcommand should show short, context-aware help: the detected repository, whether it is registered, and the next valid command. The first version should not add an interactive menu or shell. Generation remains an explicit action; if no atoms exist, Lore tells the user to run `lore scan` first.

## Resolution rules

Apply the same shared resolver to commands that act on one project:

1. `generate --atom <id>` uses that atom's project. If `--project` is also provided, validate that the atom belongs to it and explain any mismatch.
2. Otherwise, an explicit `--project` overrides the current directory.
3. Otherwise, when the working directory is inside a Git repository, resolve its Git top-level path and select the registered project with that path.
4. If the repository is not registered, ask for confirmation in an interactive terminal, register the detected Git root using the existing project inspection flow, then continue. On a name collision, ask for a distinct display name. In non-interactive use, do not prompt or write to the registry; tell the user to run `lore project add .` from the Git root and show that root path.
5. Without an explicit project or Git repository context, retain current behavior for list and scan commands. For generation, preserve the implicit choice only when all available atoms belong to one project; when atoms span multiple projects, require an explicit `--project` or `--atom` and explain how to choose one.
6. `lore scan --all` remains the explicit batch operation and overrides current-directory detection; reject combining it with `--project` so the scope is never ambiguous. When inside a repository, plain `lore scan` means the current repository.

Use `git -C <cwd> rev-parse --show-toplevel` through an argument list to discover the root. Canonicalize paths before comparing them with registered paths. This handles nested directories and worktrees without treating `.git` as a directory. Add a database lookup by canonical path; the existing unique path constraint should be sufficient, so avoid a schema migration or project-local config file.

### Install route decision

| Route | What the user installs | Fit for the target workflow | Tradeoff |
|---|---|---|---|
| **Recommended to validate: pipx from GitHub** | One isolated user-level Lore install from the repository | Puts `lore` on the user's PATH so it works from other repositories | Depends on supported Git/VCS installation and a clear upgrade command; validate on macOS/Linux and Windows before recommending it |
| Existing clone + virtual environment | A checkout-local install | Works today and remains useful for contributors | The command is only available when the environment is active or its executable path is used |
| PyPI release | A published package install | Simplest install and upgrade experience | Publication is a separate release decision and is outside this implementation plan |

Keep the supported source-install route until the global installer passes clean-install and upgrade checks. Pin the beta install to an explicit branch or release tag after choosing the release policy; do not silently track an unstable ref in user instructions.

### Command scope

- Use current-project defaults for `scan`, `atoms`, `generate`, `drafts`, `calendar`, terminal `review`, and `export`.
- Add `--project` filtering to terminal `review` and `export`, which currently operate across projects. Keep `review --web` global in this slice; reject `--project` combined with `--web` with a clear explanation until dashboard filtering is implemented separately.
- Keep `draft show/edit/approve/reject`, `config`, `voice`, and project-management commands explicit or user-wide as they are today.
- Preserve `--project` as an override wherever it already exists, with the `generate --atom` ownership check above. Keep `--all` for scanning every registered project and reject using both scan scope flags together.
- Keep the web dashboard's all-project behavior unchanged in this slice; dashboard filtering can be planned separately.

## Implementation slices

### 1. Shared repository resolver

- Add one resolver used by all project-scoped CLI commands.
- Resolve the Git root from the current working directory, normalize it, and match it against the project registry.
- Add a database method for lookup by normalized path and clear handling for missing, conflicting, or stale registry entries.
- Unit-test normal repositories, nested working directories, Git worktrees, path normalization, and a display-name collision when two different repositories share a basename.

### 2. Project-aware command defaults

- Apply the precedence rules to scanning, atom/draft listing, generation, calendar, review, and export.
- Ensure generation only considers atoms belonging to the resolved project. Add project filters to review and export.
- Preserve explicit project overrides and batch scan behavior. Avoid changing provider configuration or generation prompts.
- Add CLI integration tests that register two repositories and prove commands in either directory operate on the matching one.

### 3. First-use setup and global installation guidance

- Add a confirmation step when an interactive user invokes a project-scoped command in an unregistered repository. Reuse `lore project add .` and `ProjectWalker` rather than inventing a second registration path.
- In non-interactive use, fail with a copyable setup command and make no registry changes.
- Add concise no-argument help showing current repository context and next steps.
- Validate and document a user-level installer for beta users, with `pipx` installing the GitHub source as the proposed default. Keep the repository virtual-environment install for contributors. PyPI publication is separate and requires separate release approval.
- Document macOS/Linux and PowerShell command availability, including how to upgrade the global install.

### 4. End-to-end verification and release notes

- Run the full test suite and package build.
- Install using the documented user-level route in a temporary tool environment, invoke `lore` from outside the Lore checkout, then verify installation and upgrade from both a repository root and nested directory.
- Verify the no-project, unregistered-repository, non-interactive, explicit `--project`, and `--all` cases.
- Update README, BETA.md, and CONTEXT.md to match the implemented behavior. Do not claim a PyPI release unless one is separately approved and published.

## Acceptance criteria

- A user can install Lore once and run its command while their shell is in another project.
- From a registered repository or any nested directory, project-scoped commands use that repository without requiring `--project`.
- An unregistered repository is never silently added: interactive use asks first; non-interactive use gives a setup command and makes no changes.
- If the user runs a command from a nested directory, registration targets the Git root rather than the nested directory.
- A command in one repository cannot select another repository's atom for generation by accident.
- `--project` overrides current-directory detection, and `scan --all` still scans all registered projects.
- `generate --atom` cannot silently conflict with `--project`; the CLI explains a mismatch rather than crossing project boundaries.
- Git worktrees and paths containing spaces resolve correctly.
- No source diffs are added to the scan-to-generation prompt, and no command publishes content.
- Existing explicit project workflows continue to work, and package installation exposes the `lore` command outside the source checkout.

## Risks and decisions for review

- **Global install availability:** the package is not on PyPI. The plan adds beta installation guidance from the repository; publishing remains a separate release decision.
- **Installer support:** confirm `pipx` can install and upgrade from the GitHub source on supported macOS/Linux and Windows setups before making it the recommended route. Keep a tested source-install fallback in the docs.
- **Legacy no-project behavior:** `scan` currently scans all projects when no project is supplied. This plan changes that default only when run inside a repository; outside a repository it keeps the current behavior, while ambiguous generation must ask for an explicit project.
- **Registration prompt:** only interactive sessions can prompt. Automation must use the explicit `lore project add .` setup first.
- **Dashboard scope:** the web review dashboard remains global in this slice, while terminal review uses the current project. Keep that distinction clear in help text.

## Out of scope

- PyPI publication or a public release.
- Automatic generation, remote-provider calls during scanning, or automatic publishing.
- Per-project model credentials or configuration files.
- Reading source diffs or changing the current privacy boundary.
- Dashboard visual redesign or repository-specific dashboard filtering.
