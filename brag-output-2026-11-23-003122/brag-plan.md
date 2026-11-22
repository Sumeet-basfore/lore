# Brag Plan: Lore

## Planning rubric

1. **What is the app?** Lore is a local-first developer CLI that turns recent Git commit metadata into editable engineering-content drafts, with a local review and export workflow.
2. **Strongest claim:** “Turn recent Git history into a draft you can edit and export.” It describes the shipped flow without promising draft accuracy or quality.
3. **Visual hook:** A blank writing surface resolves into the selected Evidence Strata mark, then into Lore’s real dark review interface.
4. **UI to show:** The actual command sequence and a faithful recreation of the loopback review dashboard. Demo text and records are conspicuously marked “Illustrative sample.”
5. **Shortest satisfying video:** 20.4 seconds: enough time to show scan, generation, review, and export without adding future capabilities.
6. **Tone:** default; clean, calm, and human, with one dry observation about the blank post. Motion stays restrained and follows Lore’s clear-workbench brand.
7. **Audio:** A steady, low-volume music bed with a few warm, quiet UI cues. No voiceover.
8. **Share caption:** “Lore turns recent Git history into an editable engineering draft you can review and export. Built for the moment after you ship and before you write the post. Music: Sascha Ende, ende.app (CC BY 4.0).”
9. **User flow:** lore scan → lore generate --platform linkedin → inspect/edit/approve in lore review → lore export. lore image generate <draft-id> adds an editable SVG illustration to a saved draft.

## What is this app?

Lore reads Git commit metadata, groups related changes into content atoms, and generates drafts for formats such as LinkedIn, X, blogs, and changelogs. People review and export drafts locally. It does not publish posts from the CLI.

## The angle

The work already happened; writing about it can start from the Git history instead of an empty editor. Show Lore gathering commit metadata, making a draft and editable vector illustration, then handing the result back to the person for review and export. Keep the demo grounded in current beta behavior.

## Hook (first 2–3 seconds)

Start on a quiet, blank writing surface. Reveal “The work shipped.” followed by “The post is still blank.” The Evidence Strata mark appears as the writing surface turns into a compact developer workbench.

## Key moments (the middle)

- The real scan command leads into “Content Atoms · Engineering Accomplishments,” with an explicit “Commit metadata” label.
- The real LinkedIn generation and SVG illustration commands sit beside an illustrative draft preview. The sample is labeled throughout.
- A faithful dashboard view shows Draft Content, Evidence & Diff Card, and the actual Edit, Approve, Reject, and Copy actions. All record values are illustrative.

## Outro / punchline

Show the actual export command, then the canonical SVG mark and: “Recent Git history. A draft you can shape.”

## User flow worth showing

Repository → scan commit metadata → generate an editable draft → review and approve → export locally. Image generation is an optional step for a saved draft. The video must not imply account connections, scheduling, publishing, analytics, or source-diff analysis in the normal scan-to-draft flow.

## Tone

- **Preset:** default
- **Creative direction:** clear workbench; lightly dry opening, useful product demonstration, no launch-hype language.
- **Interpretation:** Five compact beats with readable holds and calm transitions. The copy stays factual; the dashboard and selected logo carry the product identity.

## Format: landscape — 1920×1080

## Duration: 20.4 seconds

## Visual identity (from the project)

- **Background:** marketing paper #F4F7F8; dashboard canvas #090D13
- **Accent:** action green #1F7A3B; dashboard accent #58A6FF
- **Text:** marketing ink #0B0F14; dashboard text #C9D1D9
- **Logo colors:** preserve the canonical SVG unchanged (#0B0F14, #E6EDF3, #3FB950, #F85149)
- **Display/body font:** system sans fallback for this video; the specified Bricolage Grotesque and Source Sans 3 web files are not bundled. Commands use a system monospace stack, matching the dashboard’s fallbacks.
- **Strongest visual element:** Evidence Strata logo and the existing dark review gateway, with a restrained cool-paper frame around it.

## Share copy (draft)

Lore turns recent Git history into an editable engineering draft you can review and export. Built for the moment after you ship and before you write the post. Music: Sascha Ende, ende.app (CC BY 4.0).

## Audio direction

- **Role:** Low, clean support under the product demo.
- **Music:** happy-beats-business-moves-vol-12-by-ende-dot-app.mp3, steady and polished; use a restrained bed around 0.28 volume.
- **Music treatment:** Begin under the opening, keep it level during command and review beats, then fade at the final logo.
- **Music cue guidance:** Bundled preset at assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json; estimated 109.96 BPM. Land the draft reveal near 8.74s, review reveal near 13.11s, and logo near 17.47s. Cues guide timing only; text readability takes priority.
- **Audio-reactive treatment:** Subtle only; a small accent rule may breathe slightly with the music. No waveform, particles, glow, or visualizer.
- **SFX posture:** Sparse and warm. A soft click can accompany a real edit/approve action; one quiet, soft impact can land on the logo.
- **Audio-coupled moments:** command entry, approval action, final logo reveal.
- **Restraint rule:** No typing-per-character sound barrage or large cinematic impacts.

## Storyboard

### Scene 1 — The blank post — 2.7s

An empty writing canvas holds for a beat. “The work shipped.” appears, then “The post is still blank.” The Evidence Strata mark resolves at the edge of the canvas.

Sequential/interaction: Yes — two short lines arrive and hold long enough to read.
Audio intent: Establish a calm, human moment; music begins quietly.
Audio-coupled idea: One soft text arrival, no repeated key clicks.
Transition mood: Clean slide into the scan workbench.

### Scene 2 — Scan — 5.1s

The command lore scan --since "14 days ago" appears in a terminal panel. A restrained ledger view follows, titled “Content Atoms · Engineering Accomplishments,” with the visible label “Commit metadata.” No fabricated counts or author details.

Sequential/interaction: Yes — command, then the ledger title and metadata label.
Audio intent: Precise, useful, and unhurried.
Audio-coupled idea: One low-risk click for the command; rows resolve in a short stagger and then hold.
Transition mood: Soft crossfade to the draft.

### Scene 3 — Draft and illustration — 5.3s

At 8.74s, show lore generate --platform linkedin. Beside it, show lore image generate <draft-id> and a geometric SVG preview. A persistent “Illustrative sample” label accompanies the sample copy: “Turn recent Git metadata into copy you can edit.”

Sequential/interaction: Yes — generation command first, then labeled sample draft, then vector preview.
Audio intent: The draft is the payoff; keep the music beneath it.
Audio-coupled idea: Align the draft card reveal near the 8.74s strong cue; keep sample text settled for at least 2.7s.
Transition mood: Soft crossfade into the real review layout.

### Scene 4 — Human review — 4.4s

At 13.11s, recreate the dashboard from src/lore/approval/local_web.py: left draft queue, action bar, Draft Content panel, and Evidence & Diff Card panel. Show the real E Edit and A Approve controls. Any title, draft ID, status, or body is labeled as illustrative. The line “Review stays in your hands.” is short and readable.

Sequential/interaction: Yes — select the sample draft, edit, then approve; do not show a post being published.
Audio intent: A clear handoff to human judgment.
Audio-coupled idea: One soft click for approve; no success fanfare.
Transition mood: Clean cut into export.

### Scene 5 — Export and mark — 2.9s

Show lore export --status approved --format markdown --output-dir ./exports, then the canonical SVG mark and “Recent Git history. A draft you can shape.” The repo beta guide may appear as a small, readable GitHub CTA.

Sequential/interaction: Yes — export command, logo, final line.
Audio intent: Warm, compact finish.
Audio-coupled idea: Land the logo at the 17.47s strong cue; allow the final line to hold.
Transition mood: Fade to the canonical mark.

**Music mood for this video:** steady and clean.
**Audio summary:** A restrained instrumental bed supports the flow, with one quiet command click, one approval click, and a soft final logo accent.
