# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Convert the arc42 + LASR conference talk (originally in `arc42AndLasr_talk - envite_original.pptx` / `.pdf`) into a **Reveal.js presentation** hosted as a GitHub Page (domain in `docs/CNAME`).

Key constraints:
- **No company references**: remove all mentions of novatec, envite (incl. logo,
  tagline "Pioneering IT Sustainability", contact data), or any employer.
- **No specific conference references**: remove IT-Tage, Software Quality Days,
  decompiled, or any named event.
- The presentation must look and behave as close to the PPTX as possible:
  exact shape positioning (no visual jumps between slides or animation steps)
  and PowerPoint click animations rebuilt as Reveal.js fragments.
- Track decisions in `docs/progress.md`.

## How the presentation is built

`docs/index.html` is **generated — do not edit it by hand.** All rendering
fixes belong in the generator:

```bash
pip install -r scripts/requirements.txt

# regenerate docs/index.html, docs/css/custom.css and docs/img/ from the PPTX
python3 scripts/pptx2reveal.py \
    "arc42AndLasr_talk - envite_original.pptx" docs \
    "arc42AndLasr_talk - envite_original_rendered.pdf"

# visual regression: screenshot every slide and diff against the rendered PDF
python3 scripts/compare_render.py            # all slides
python3 scripts/compare_render.py --slides 5,12   # subset
```

`scripts/pptx2reveal.py` translates DrawingML (shape coordinates in EMU,
style inheritance through layout/master/theme, fills, tables, SmartArt,
connectors, custom geometry) into absolutely positioned HTML on a 960×540
canvas, converts `p:timing` entrance animations into fragments, extracts
media into `docs/img/` (descriptive names via `MEDIA_SLUGS`/`PDF_SLUGS`,
deduplicated by content), pulls backgroundRemoval bitmaps
out of the rendered PDF, and filters all banned company/conference references
(`BANNED_RE`, `BANNED_MEDIA`, `TEXT_REPLACEMENTS` at the top of the script).

`scripts/compare_render.py` serves `docs/`, screenshots each slide with
headless Chromium (Playwright, executable at
`/opt/pw-browsers/chromium-*/chrome-linux/chrome`) in its final fragment
state and writes reference/actual/diff composites to `screenshots/compare/`
plus an RMS score per slide. Reference pages live in `work/ref_pdf/`
(rendered once from the original PDF via PyMuPDF at 960×540).

Known accepted deviation: PowerPoint's PDF export flattens white
alpha-gradient overlays (slides 1 and 53) to near-solid white; the live
render (like LibreOffice) shows the underlying photo through the gradient.

## Project Structure

```
docs/               ← GitHub Pages root (serves index.html)
  index.html        ← GENERATED presentation (all 53 slides)
  css/custom.css    ← GENERATED base styles
  img/              ← GENERATED slide media (descriptive file names)
  fonts/            ← self-hosted DM Sans + Karla woff2 + fonts.css
  dist/             ← reveal.js compiled assets
  CNAME             ← GitHub Pages custom domain (maintained by the user)
  progress.md       ← decision log (source of truth across sessions)
scripts/
  pptx2reveal.py    ← PPTX → Reveal.js generator
  compare_render.py ← screenshot/diff verification harness
work/               ← scratch space (gitignored): unzipped pptx, ref renders
```

## Reveal.js Conventions

- `Reveal.initialize`: `width: 960, height: 540, margin: 0, hash: true,
  slideNumber: "c/t", history: true, mouseWheel: true, transition: 'fade',
  navigationMode: "linear"`.
- One top-level `<section>` per PPTX slide, attributes `data-pptx` (source
  slide xml) and `data-page` (PDF page).
- Shapes are absolutely positioned divs inside `<div class="pcanvas">`;
  fragments carry `data-fragment-index` (one index per PowerPoint click).
- Speaker notes: `<aside aria-label="speaker notes" class="notes">`.

## Browser / Playwright Screenshots

Always save screenshots to `screenshots/` (gitignored, never commit).

## GitHub Pages Setup

- GitHub Pages serves the `docs/` folder of the default branch; no build step.
- `docs/CNAME` holds the custom domain — the user manages its value; do not
  overwrite it.
