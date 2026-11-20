# Lore beta tester guide

Lore is a local CLI that turns Git commit history into engineering content drafts. The beta is for trying the scan, draft, review, and export workflow and reporting problems. It is not a hosted service, and it does not publish posts from the CLI.

## Set up

You need Git and Python 3.12 or newer. Install from the repository:

```bash
git clone https://github.com/Sumeet-basfore/lore.git
cd lore
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

To keep beta data separate from an existing Lore setup, set `LORE_HOME` to a new directory before running Lore. For example, on macOS or Linux:

```bash
export LORE_HOME="$HOME/.lore-beta"
```

Start onboarding with `lore init`. The default provider is Ollama at `http://localhost:11434`; have Ollama running with the selected model available. You can select OpenAI, Anthropic, OpenRouter, or Gemini instead; onboarding asks for a model name for the selected provider. For remote providers, Lore sends the generated prompt to that service. Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, or `GEMINI_API_KEY` (also `GOOGLE_AI_API_KEY`) in your shell environment or a secret manager. Lore also supports an `api_key` config value, but it is stored unencrypted in `~/.lore/config.yml` (or the directory set by `LORE_HOME`). Do not pass real keys as command-line arguments.

## Try the workflow

Choose a repository whose commit metadata and project name you are allowed to process with your configured model endpoint.

```bash
lore project add /path/to/repository --name my-project
lore scan --project my-project --since "14 days ago"
lore atoms --project my-project
lore generate --project my-project --platform linkedin
lore review
```

The review screen lets you inspect drafts and approve, reject, or edit them. You can also inspect a specific draft with `lore draft show <draft-id>`, edit it with `lore draft edit <draft-id>`, and approve it with `lore draft approve <draft-id>`. Export approved drafts with:

```bash
lore export --status approved --format markdown --output-dir ./exports
```

Other supported generation formats are `twitter`, `thread`, `blog`, and `changelog`. Run `lore --help` or `lore <command> --help` for options.

## Privacy boundaries

- `lore project add` locally inspects the README and selected project metadata files to infer a description and technology stack.
- `lore scan` reads Git commit metadata, including author details, commit subjects, timestamps, changed paths, and insertion/deletion counts. It does not read patch contents for the scan-to-draft workflow. Some known secret-like filenames are excluded by pattern, but that does not detect all secrets.
- The standalone DLP scanner in the source tree is not called by the current CLI workflow. Do not treat it as protection for your scan or generated prompts.
- Generation prompts can include the project name, commit subjects, evidence SHAs, file paths, counts, dates, technology stack, and generated style guidance. Changelog prompts include a few commit subjects. Lore does not send the full voice sample text, but stores those samples locally.
- The default Ollama URL is local. If you configure another Ollama URL or choose a cloud provider, prompt data goes to that endpoint and is subject to its policies.
- Lore stores project paths, atoms, drafts, voice samples, and configuration in local files under `~/.lore/` or `LORE_HOME`. These files are not encrypted by Lore.

Use a local Ollama endpoint if you do not want Lore to send prompts to a remote model provider. Local endpoint configuration does not make the source tree's standalone DLP scanner active.

## Review every draft

Evidence records connect a draft to Git commit SHAs, subjects, paths, and change counts. They do not verify every sentence. Lore does not know whether a change improved performance, passed tests, or had a particular user impact unless that information is present in the commit metadata and checked by you. Generated content can still be inaccurate or include unsupported details.

If the selected model is unavailable, Lore stops with an error. It does not save canned mock text as a draft. Check the commit, metric, and file claims yourself before approving or sharing an export.

## Report feedback

Open a [GitHub issue](https://github.com/Sumeet-basfore/lore/issues) with the Lore and Python versions, the command you ran, what you expected, and a sanitized error or screenshot. Do not include API keys, private diffs, customer information, or other sensitive repository data.
