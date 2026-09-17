# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

The PPTX → Reveal.js conversion is **finished**. From now on only the
Reveal.js deck under `docs/` is looked at and maintained. The PPTX, the
rendered PDF and `scripts/pptx2reveal.py` are historical artefacts:
**do not regenerate the deck from them**, and do not use them as the
reference for "correct" output any more.

Consequences:
- `docs/index.html`, `docs/slides/*.html`, `docs/css/custom.css` and
  `docs/img/` are now **hand-maintained sources**. Edit them directly.
- `scripts/pptx2reveal.py` is frozen. Running it would overwrite the
  hand-made changes.
- `scripts/compare_render.py` may still be used to screenshot slides for a
  visual check, but a diff against the old PDF is no longer a defect — the
  deck is allowed to diverge from the original.
- Keep tracking decisions in `docs/progress.md`.

Content constraints that still apply:
- **No company references**: no novatec, envite (incl. logo, tagline
  "Pioneering IT Sustainability", contact data), or any employer.
- **No specific conference references**: no IT-Tage, Software Quality Days,
  decompiled, or any named event.

## Project Structure

```
docs/               ← GitHub Pages root (serves index.html)
  index.html        ← shell: one <section> per slide that lazy-loads its
                      slides/*.html before Reveal initialises
  slides/*.html     ← slide bodies, named after the deck position
                      (slide01.html … slide52.html)
  css/custom.css    ← base styles
  img/              ← slide media
  fonts/            ← self-hosted DM Sans + Karla woff2 + fonts.css
  dist/             ← reveal.js compiled assets
  CNAME             ← GitHub Pages custom domain (maintained by the user)
  progress.md       ← decision log (source of truth across sessions)
scripts/            ← frozen conversion toolchain (see Project status)
work/               ← scratch space (gitignored)
```

## Reveal.js Conventions

- `Reveal.initialize`: `width: 960, height: 540, margin: 0, hash: true,
  slideNumber: "c/t", history: true, mouseWheel: true, transition: 'fade',
  navigationMode: "linear"`.
- One top-level `<section>` per slide, attributes `data-pptx` (source slide
  xml), `data-page` (PDF page) and `data-src` (the `slides/*.html` body,
  fetched into the section before `Reveal.initialize` runs). The `data-pptx`
  / `data-page` attributes are provenance only.
- The deck has **52 slides**, and `docs/slides/slideNN.html` is the NNth
  slide of the deck (not the source PPTX numbering). Adding or removing a
  slide means editing `docs/index.html`, adding/removing the matching
  `docs/slides/*.html` and renumbering the files after it.
- Shapes are absolutely positioned divs inside `<div class="pcanvas">` on a
  960×540 canvas; keep positions stable so there are no visual jumps between
  slides or fragment steps.
- Fragments carry `data-fragment-index` (one index per click step).
- Speaker notes: `<aside aria-label="speaker notes" class="notes">`.

## Browser / Playwright Screenshots

Always save screenshots to `screenshots/` (gitignored, never commit).

## GitHub Pages Setup

- GitHub Pages serves the `docs/` folder of the default branch; no build step.
- `docs/CNAME` holds the custom domain — the user manages its value; do not
  overwrite it.
