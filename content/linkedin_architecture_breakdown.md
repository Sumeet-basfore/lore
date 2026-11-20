# What Lore reads from a repository

Lore is a small CLI experiment around one question: can Git history give an engineer a useful starting point for writing an update?

The current scan is metadata-based. It reads commit subjects, dates, changed paths, and insertion/deletion counts. Lore groups related commits into content atoms and records commit SHAs and file paths as evidence. It does not pass source diffs to the model in the normal scan-to-draft workflow.

That evidence helps a reviewer trace where a summary came from. It does not prove that every sentence is correct or that a change improved performance. A count of changed lines is not a benchmark.

The default model endpoint is Ollama on localhost. Lore can also use remote providers. In that case, the generated prompt includes the project name, commit summaries, evidence fields, technology stack, and style guidance. Changelog prompts include commit subjects. The selected provider receives that prompt.

The repository contains a standalone DLP scanner, but the CLI workflow does not call it. Some known secret-like file names are skipped during scanning, which is not complete secret detection. For that reason, beta users should only test with repositories whose metadata they can send to their selected model endpoint.

Generated drafts are saved locally. Review them, edit unsupported details, and export only after approval. Lore does not publish from the current CLI.

This is a working beta, not a claim that AI can verify a developer's work. The useful test is whether commit metadata gives an engineer a better first draft than starting with a blank page.
