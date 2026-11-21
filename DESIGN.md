---
# gstack: design-md-format=spec
name: Lore
description: "A clear workbench for turning local Git history into editable drafts."
colors:
  background: "#F4F7F8"
  primary: "#1F7A3B"
  on-primary: "#FFFFFF"
  surface: "#FFFFFF"
  text: "#0B0F14"
  text-muted: "#52606D"
  border: "#D3DCE2"
  accent: "#1F7A3B"
  success: "#1F7A3B"
  warning: "#7A4D00"
  error: "#B42318"
  logo-background: "#0B0F14"
  logo-ink: "#E6EDF3"
  logo-green: "#3FB950"
  logo-red: "#F85149"
  dashboard-background: "#090D13"
  dashboard-surface: "#161B22"
  dashboard-header: "#11141A"
  dashboard-border: "#30363D"
  dashboard-text: "#C9D1D9"
  dashboard-muted: "#8B949E"
  dashboard-strong: "#F0F6FC"
  dashboard-accent: "#58A6FF"
  dashboard-success: "#3FB950"
  dashboard-warning: "#D29922"
  dashboard-error: "#F85149"
typography:
  display:
    fontFamily: "Bricolage Grotesque"
    fontWeight: "600-700"
    fontSize: "clamp(2.5rem, 1.5rem + 3vw, 4.5rem)"
    letterSpacing: "-0.03em"
  body:
    fontFamily: "Source Sans 3"
    fontSize: "1rem"
    lineHeight: 1.6
  label:
    fontFamily: "Source Sans 3"
    fontSize: "0.8125rem"
    letterSpacing: "0"
  mono:
    fontFamily: "JetBrains Mono"
    fontFeature: tnum
rounded:
  sm: 4px
  md: 8px
  lg: 12px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
  button-primary-hover:
    backgroundColor: "#17652F"
  input:
    borderColor: "{colors.border}"
    rounded: "{rounded.sm}"
---

# Lore

## Overview

**Creative North Star:** Make developer content easy to read, inspect and take through review.
**Product context:** Lore is a local-first developer content CLI with a loopback review dashboard. The beta turns Git commit metadata into editable drafts that people can review and export. It does not read source diffs in the scan-to-draft path or publish posts.
**Mode per surface:** Future landing page: Persuade. Local dashboard: Operate. Draft content: Read.
**Reference sites:** None; peer research was declined.
**Key characteristics:**
- Show a real draft before describing the workflow.
- Keep commit metadata visible as a separate evidence list; do not imply sentence-level links.
- Make scan, generate, review and export easy to follow.
- Show the local-first default and explain when a selected remote model receives prompts.

## Colors

**Strategy:** Restrained, with color reserved for actions and status. The future marketing surface uses the cool light tokens above; the existing dashboard retains its dark tokens from `src/lore/approval/local_web.py`.

The canonical mark keeps its original four colors. Do not recolor the SVG to fit a surface. Use the darker green token for actions on light surfaces; retain the mark’s brighter green and coral in the mark and existing dark dashboard states. Green and red are never decoration. Recheck contrast for each rendered control, focus state and disabled state before release. The proposed ink, muted text and green action pairs on the marketing background calculate to 17.85:1, 6.00:1 and 4.99:1 respectively.

## Typography

Use Bricolage Grotesque for display, Source Sans 3 for prose and interface text, and JetBrains Mono for commands, hashes and evidence metadata. The official Google Fonts records list these families under OFL; variable ranges are Bricolage Grotesque 200–800, Source Sans 3 200–900 and JetBrains Mono 100–800. Use display weights 600–700, body/UI 400–600 and mono 400–500. Sources: [Bricolage Grotesque](https://github.com/google/fonts/blob/main/ofl/bricolagegrotesque/METADATA.pb), [Source Sans 3](https://github.com/google/fonts/blob/main/ofl/sourcesans3/METADATA.pb), [JetBrains Mono](https://github.com/google/fonts/blob/main/ofl/jetbrainsmono/METADATA.pb).

When web surfaces adopt these fonts, self-host WOFF2 files sourced through the [Google Fonts CSS API](https://developers.google.com/fonts/docs/getting_started), include the OFL notices and make no runtime font request from the local dashboard. The font files are not bundled yet. Keep generic `sans-serif` and `monospace` fallbacks.

## Layout

Use a 4px spacing rhythm. Give prose a 64–72 character measure and let evidence rows stay compact. The dashboard remains task-focused, with the draft and evidence ledger adjacent but distinct. A future landing page should lead with a genuine Lore draft and its commit metadata, then show the actual CLI steps. Do not invent paragraph-to-commit connections. At narrow widths, stack the evidence list after the draft.

## Elevation & Depth

Use surface contrast and thin borders to define regions. Avoid shadows, glows, blurred layers and nested cards.

## Shapes

Use 4px corners for inputs, 8px for buttons and larger work regions up to 12px. Keep evidence rows and separators square. Avoid pill buttons.

## Components

Primary actions use the primary token, clear verbs and visible keyboard focus. Status includes text as well as color. Keep approve, reject and export actions distinct. Preserve the dashboard’s existing behavior unless a separate UI change is approved.

## Brand and voice

Use `src/lore/approval/logo.svg` as the canonical full-color mark. Do not crop, stretch, outline or recolor it. Keep clear space around it and render at 32px or larger in product UI; keep CLI output text-only. A GitHub README may reference the SVG; export a PNG/JPG for the repository social preview. See [GitHub README image guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) and [social preview requirements](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).

Use plain, specific copy. A suitable product description is: “Turn recent Git history into a draft you can edit and export.” Demonstrate the desired content quality with a genuine output rather than claiming it. Label illustrative examples. Say “commit metadata,” not “source code analysis.” Do not promise accuracy, complete secret detection, privacy with a remote provider, human-sounding prose or publishing. State that Lore does not publish posts.

## Do's and Don'ts

- Do make the real scan → generate → review → export flow visible.
- Do label examples as illustrative unless they came from a real run.
- Do state that remote providers receive prompts when selected.
- Don't invent metrics, testimonials, user counts or unshipped UI behavior.
- Don't use gradients, glow, decorative icon grids, fake terminal output or unsupported product claims.

## Motion

- **Approach:** Minimal-functional.
- **Easing:** Short ease-out for entry; ease-in-out for state changes.
- **Duration:** 120–180ms for small state changes; no staged hero choreography.
- **The one authored moment:** A subtle highlight when selecting a draft, with the final state shown immediately when reduced motion is preferred.

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-11-21 | Evidence Strata is the canonical mark; clear-workbench system approved | Keep the logo fixed and let real draft content carry the first impression. |
| 2026-11-21 | No competitor research or visual preview | The user chose to work from Lore’s context and skip the preview. |
