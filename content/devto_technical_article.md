---
title: What Lore Reads From Your Git History
published: false
tags: python, git, developer-tools
---

Lore is a command-line experiment for turning recent Git history into a draft engineering update. Before asking a beta tester to try it, it helps to be precise about what it reads and what the evidence means.

## The current input is commit metadata

The normal scan reads Git log metadata: commit subjects, dates, changed paths, and insertion/deletion counts. Lore groups commits into content atoms and records commit SHAs, paths, and counts. It does not read source diffs for the scan-to-draft workflow.

That design has a useful limit and a clear trade-off. Prompts contain less source material, but a vague commit message may not explain why a change was made. A count of changed lines does not show performance, correctness, or user impact.

## Evidence is a trail, not proof

A draft can point back to the commits and metadata used to construct its atom. That helps the author inspect the source of a claim. It does not check every generated sentence. The model can add details that were never present in the evidence, so review remains part of the workflow.

## Where prompts go

Lore defaults to an Ollama endpoint on localhost. It can also use OpenAI, Anthropic, OpenRouter, Gemini, or another configured Ollama endpoint. A generation prompt can include the project name, commit subjects, evidence SHAs, changed paths, counts, dates, technology stack, and generated style guidance. Changelog prompts include commit subjects.

When a remote provider is selected, that provider receives the prompt. Lore stores projects, atoms, drafts, voice samples, and configuration locally. A configured API key is stored without encryption in the local YAML file.

## Secret detection is limited

Some file names that look sensitive are skipped. A separate DLP scanner exists in the repository, but the current CLI scan-to-draft workflow does not call it. This is not a complete secret detection system. Beta users should test with repositories whose metadata can be sent to the chosen model endpoint.

## The beta workflow

The CLI supports scanning, generating a draft, reviewing and editing it, and exporting it. It does not publish posts from the CLI. The beta is intended to find where the workflow is confusing, where the summaries lose context, and what reviewers need to see before trusting an export.

If you try Lore, review each generated claim before sharing it and report problems through a GitHub issue. Do not include private diffs, API keys, or customer data in a report.
