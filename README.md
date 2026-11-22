# Lore

<p><img src="src/lore/approval/logo.svg" alt="Lore logo: evidence spine and diff strata" width="64"></p>

Lore is a local-first CLI for turning recent Git history into engineering content drafts. It starts from commit metadata and evidence summaries, then lets you inspect, edit, and export a draft.

<p>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.12+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3.12 or newer"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="MIT License"></a>
</p>

<p align="center">
  <img src="assets/readme/lore-review-preview.png" alt="Illustrative preview of Lore's local review dashboard with sample draft data" width="100%">
</p>
<p align="center"><em>Illustrative dashboard preview. The draft and record values shown are sample data.</em></p>

**Beta:** Install Lore from source; the package is not published to PyPI. See the [beta tester guide](BETA.md) for the workflow and privacy details.

[Quickstart](#quickstart) · [Capabilities](#what-the-current-cli-does) · [Privacy](#privacy-and-data-handling) · [Feedback](#feedback)

## Install

Requirements: Python 3.12 or newer and Git.

### macOS and Linux

```bash
git clone https://github.com/Sumeet-basfore/lore.git
cd lore
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install .
lore --help
```

### Windows PowerShell

```powershell
git clone https://github.com/Sumeet-basfore/lore.git
cd lore
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\lore.exe --help
```

These commands use the Python 3 version selected by the launcher and avoid environment activation, which PowerShell execution policy can block. The quickstart assumes `lore` is on your PATH; activate the source virtual environment before changing into the target repository, or use the user-level pipx install below.

### Install a user-level `lore` command (beta)

To use `lore` from any repository, install the GitHub source with [pipx](https://pipx.pypa.io/). Lore is not published to PyPI yet. Install pipx and Git first, then run:

```bash
pipx install "git+https://github.com/Sumeet-basfore/lore.git@main"
pipx ensurepath
```

Open a new terminal if `lore` is not on your `PATH`. PowerShell uses the same commands. To refresh the beta install after a source update, run:

```bash
pipx install --force "git+https://github.com/Sumeet-basfore/lore.git@main"
```

The checkout-and-virtual-environment instructions above remain useful for contributors. Activate that environment before changing into another project directory.

## Quickstart

### 1. Scan the repository you are in

```bash
lore init
cd /path/to/repository
lore scan --since "14 days ago"
lore atoms
```

On first use in an unregistered Git repository, Lore asks before adding it. For non-interactive use, run `lore project add . --name my-project` from the repository root. An explicit `--project` still overrides the current repository, and `lore scan --all` scans every registered project.

### 2. Generate and review a draft

```bash
lore generate --platform linkedin
# Replace <draft-id> with the ID printed by `lore generate`.
lore draft show <draft-id>
lore image generate <draft-id>
lore draft edit <draft-id>
lore draft approve <draft-id>
```

Image generation saves an editable SVG under `lore-media/` in the project and attaches it to the draft for preview in `lore review --web`. Add `--format png` when you need a raster image for a social platform; PNG conversion uses an optional local renderer and keeps the SVG source alongside it. Use `--force` to replace an existing image.

You can also list drafts with `lore drafts`, review pending drafts in the terminal with `lore review`, or open the local dashboard with `lore review --web`. The dashboard binds to loopback on `127.0.0.1`. With no subcommand, `lore` shows the current repository and suggested next commands.

On Windows PowerShell, if `EDITOR` is not set, configure the built-in Notepad editor before using `lore draft edit`:

```powershell
$env:EDITOR = "notepad"
```

### 3. Export the approved draft

```bash
lore export --status approved --format markdown --output-dir ./exports
```

`lore init` defaults to Ollama at `http://localhost:11434`; start Ollama and install the selected model before generating. Lore also supports OpenAI, Anthropic, OpenRouter, and Gemini. When you select a remote provider, it receives the generation prompt described in [Privacy and data handling](#privacy-and-data-handling).

## What the current CLI does

- Reads Git commit metadata for the selected time range: commit subjects, dates, changed file paths, and insertion/deletion counts.
- Groups related commits into content atoms and records commit SHAs, file paths, and change counts as evidence.
- Generates drafts for Twitter/X, X threads, LinkedIn, blogs, and changelogs using the configured model.
- Creates an editable, geometric SVG illustration from a saved draft and its linked evidence summary; optionally exports a PNG for platforms that require raster images.
- Renders Git diff cards as SVG by default with `lore card`; an explicit `.png` output requires a local rasterizer.
- Saves projects, atoms, drafts, and voice samples in a local SQLite database under `~/.lore/` (or `LORE_HOME`).
- Lets you edit, approve, reject, and export drafts. Review each factual claim before using it.

The CLI scan-to-draft workflow does not read source files or patch contents. A separate DLP scanner exists in the repository, but it is not connected to this workflow. The scan filters some known secret-like file names; that is not a complete secret detection system.

## Privacy and data handling

- Scanning runs Git locally. It reads commit metadata, including author information, but the generated atoms use commit subjects, file paths, counts, dates, and SHAs.
- Generation sends a prompt containing the project name, selected atom and commit summaries, evidence fields, technology stack, and generated style guidance. Changelog prompts also include commit subjects. Voice sample text stays in the local database; Lore derives brief style guidance from it for the prompt.
- Image generation sends the project name, platform, draft title and a short excerpt, linked atom title/summary, and evidence counts to the configured model. It does not send source files or patch contents. A remote provider receives this prompt when selected. The SVG markup is rendered locally from a restricted set of geometric shapes.
- With the default Ollama URL, Lore sends the prompt to the local Ollama endpoint. If you configure a remote Ollama endpoint or select OpenAI, Anthropic, OpenRouter, or Gemini, prompt data is sent to that service under its terms.
- Lore stores project paths, atoms, drafts, voice samples, and configuration locally. The SQLite database is `~/.lore/lore.db`; configuration is `~/.lore/config.yml`. A key saved in config is stored there without encryption. Prefer provider environment variables for API keys and protect your local account and files.
- Lore does not currently publish drafts from the CLI. The beta workflow ends with review and local export.

Do not use Lore with a repository if its commit metadata, file names, project name, or voice-derived style guidance must not be sent to the model endpoint you selected. The DLP module is not active in the scan-to-draft path.

## Limits to keep in mind

Generated text and illustrations can still be misleading or inaccurate. Evidence links drafts to Git records and counts; it does not prove every sentence or that an illustration represents the change correctly. Inspect each draft and image before approving or sharing them.

The CLI reads commit metadata rather than source diffs. It can miss the reason behind a change when commit messages are vague, and its change counts do not establish impact or performance. Lore does not verify metrics, infer test outcomes, or guarantee that a draft sounds human.

With normal settings, if the selected model is unavailable, generation stops with an error instead of creating a sample draft. `LORE_MOCK_LLM=1` is an explicit test mode that returns canned example text; do not use its output as project content.

## Feedback

For beta feedback or bug reports, open a [GitHub issue](https://github.com/Sumeet-basfore/lore/issues). Include the Lore version, Python version, command used, and a sanitized error message. Do not attach API keys, private diffs, or customer data.

## License

MIT. See [LICENSE](LICENSE).
