# Hyperframes Composition Brief: Lore

## Objective

Create a short launch-style demo of Lore’s current local workflow: Git metadata to editable draft to human review and local export.

## Output

- **Composition directory:** brag-output-2026-11-23-003122/composition/
- **Rendered video:** brag-output-2026-11-23-003122/brag.mp4
- **Poster:** brag-output-2026-11-23-003122/brag.jpg
- **Format:** landscape — 1920×1080
- **Duration:** 20.4 seconds

## Source material

- **Project root:** repository root
- **Primary files read:** README.md, BETA.md, DESIGN.md, src/lore/cli.py, src/lore/approval/local_web.py, src/lore/approval/logo.svg, src/lore/visual/illustration.py
- **Product name:** Lore
- **Strongest claim:** “Turn recent Git history into a draft you can edit and export.”
- **Key UI moment:** local review gateway with the draft queue, Edit/Approve/Reject/Copy actions, Draft Content, and Evidence & Diff Card panels.
- **Verbatim commands:** lore scan --since "14 days ago"; lore generate --platform linkedin; lore image generate <draft-id>; lore export --status approved --format markdown --output-dir ./exports
- **Privacy/content rule:** Do not display real commit history, author details, customer records, API keys, paths from a personal project, or local URLs. Demo content is invented and carries a persistent “Illustrative sample” or “Illustrative data” label.

## Creative direction

- **Tone preset:** default
- **Creative direction:** clear workbench with a lightly dry hook and a useful, exact product demo.
- **Interpretation:** Five concise beats; calm movement, clear typography, no speculative product claims.
- **Angle:** Start with the blank post after work ships. Show Lore collecting Git commit metadata, drafting, offering an editable SVG illustration, then returning control to a person for review and export.
- **Hook:** “The work shipped. The post is still blank.”
- **Outro:** Canonical Evidence Strata mark; “Recent Git history. A draft you can shape.”
- **Avoid:** publishing claims, source-diff analysis claims, unsupported metrics, fake testimonials, abstract tech effects, dense text, invented UI behavior.

## Visual identity

- **LOOK:** Clear workbench — cool editorial paper around a faithful dark review dashboard; square evidence rules, quiet green actions, and restrained transitions.
- **Marketing background:** #F4F7F8; ink #0B0F14; muted #52606D; action green #1F7A3B; border #D3DCE2.
- **Dashboard background/surface:** #090D13 / #161B22; dashboard text #C9D1D9; muted #8B949E; accent #58A6FF.
- **Logo:** Use the canonical source SVG unchanged. Keep its own #0B0F14, #E6EDF3, #3FB950, and #F85149.
- **Typography:** Use system sans fallbacks and system monospace. Bricolage Grotesque and Source Sans 3 WOFF2 files are not bundled in Lore; avoid remote font requests.
- **References:** DESIGN.md, src/lore/approval/local_web.py, src/lore/approval/logo.svg.

## Storyboard

Follow brag-plan.md as the creative contract. Duration total: 20.4s.

1. The blank post — 2.7s — hook text resolves on a quiet paper canvas.
2. Scan — 5.1s — actual scan command and metadata-ledger concept.
3. Draft and illustration — 5.3s — actual generation commands and clearly labeled sample draft/vector.
4. Human review — 4.4s — faithful dashboard recreation with illustrative values and actual action names.
5. Export and mark — 2.9s — export command, canonical logo, concise tagline.

## Audio

- **Audio role:** low, clean music under the product demo.
- **Audio arc:** quiet opening, steady workbench middle, soft logo close.
- **Music:** assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3
- **Music treatment:** about 0.28 volume, fade in at start and fade out on the final mark.
- **Cue guidance:** use assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json; optional strong cues at 8.74s, 13.11s, and 17.47s. Keep text holds readable.
- **Audio-reactive treatment:** subtle brightness change on an existing accent rule only; no waveform or generic visualizer.
- **Audio-coupled moments:** command entry, approve action, logo reveal.
- **SFX guidance:** sparse soft UI click and soft impact, matched to visible actions.
- **SFX analysis:** /home/sumeet/.codex/plugins/cache/brag/brag/0.6.0/skills/brag/assets/sfx/sfx-analysis.md; choose low-risk polished sounds.
- **Audio files:** copy only the selected track and SFX into composition/assets/. Include music attribution in share-copy.txt.

## Hyperframes instructions

Use the loaded HyperFrames composition, registry, and CLI contracts. Query the registry before authoring a terminal panel; use a fitting component if available. Use deterministic, seekable motion and local assets. Run npx hyperframes check and inspect sampled frames. Open the Studio preview and wait for approval before the final render. Keep all creation local; do not publish or upload the video.
