# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Convert the arc42 + LASR conference talk (originally in `arc42AndLasr_talk - envite_original.pptx` / `.pdf`) into a **Reveal.js presentation** hosted as a GitHub Page at **arc42AndLasr.marmer.online**. The presentation must look and behave as close to the original PPTX as possible.

Key constraints:
- **No company references**: remove all mentions of novatec, envite, or any employer.
- **No specific conference references**: remove IT-Tage, Software Quality Days, decompiled, or any named event.
- The presentation is **generated**, not hand-written — change `scripts/build_presentation.py`, then regenerate; never hand-edit `docs/index.html` or `docs/img/slide-NN.svg`.
- Track decisions in `docs/progress.md` (see below).

## How the Presentation Is Built

`scripts/build_presentation.py` is the single source of the presentation:

1. Opens the rendered PDF of the original talk (`arc42AndLasr_talk - envite_original_rendered.pdf`, 53 pages — the PPTX's 53 visible slides; PPTX slides 2, 3, 4, 6, 18, 30 are hidden and excluded).
2. Strips company branding: the logo image on every page, the tagline on the first/last page, the company e-mail (replaced with the private one, typeset in the bundled Karla font), and the vCard QR code (regenerated without company data).
3. Exports every page as a vector SVG (`docs/img/slide-NN.svg`, text rendered as paths → no font dependencies in the browser).
4. Extracts slide titles and speaker notes from the PPTX and generates `docs/index.html` with one full-bleed `<section>` per slide.
5. Fails the build if any banned reference remains in the page text or the speaker notes.

```bash
pip install -r scripts/requirements.txt
python3 scripts/build_presentation.py
```

## Project Structure

```
docs/               ← GitHub Pages root (serves index.html)
  index.html        ← generated presentation (do not hand-edit)
  dist/             ← reveal.js compiled assets (reset.css, reveal.css, reveal.js, dist/plugin/*)
  css/
    custom.css      ← full-bleed slide layout for the SVG slides
  img/              ← generated slide SVGs (slide-01.svg … slide-53.svg)
  CNAME             ← arc42AndLasr.marmer.online
  progress.md       ← progress/decision log (source of truth across sessions)
scripts/
  build_presentation.py  ← the whole build pipeline
  requirements.txt       ← PyMuPDF, python-pptx, qrcode, Pillow
  assets/Karla.ttf       ← font for the replacement e-mail text (OFL licensed)
```

## Development Commands

```bash
# regenerate the presentation after changing the build script
python3 scripts/build_presentation.py

# serve docs/ locally
cd docs && npm install && npm start    # → http://localhost:8000
# (or: python3 -m http.server 8000 inside docs/)
```

No test command is needed for the presentation itself; browser inspection is the verification step.

## Reveal.js Conventions

- **Reveal.initialize config**: `width: 960`, `height: 540`, `margin: 0`, `controls: false`, `progress: false`, `hash: true`, `slideNumber: "c/t"`, `history: true`, `mouseWheel: true`, `transition: 'fade'`, `navigationMode: "linear"`.
- **Section structure**: one top-level `<section>` per original slide, strictly linear (matches the PPTX, which models build-up animations as consecutive near-identical slides — the fade transition reproduces the build effect).
- **Slide content**: exactly one `<img class="slide-img">` per section pointing at `./img/slide-NN.svg`; slide 1 uses `src` (eager), all others `data-src` (reveal.js lazy loading).
- **Speaker notes**: `<aside aria-label="speaker notes" class="notes">` inside each section, taken from the original PPTX.
- **Plugins loaded**: RevealMarkdown, RevealHighlight, RevealNotes, RevealSearch, RevealZoom.

## Progress Tracking

`docs/progress.md` is the authoritative log. At the start of every session, read it to know the current state. Record noteworthy decisions there (it is a decision log now; the slide list is complete).

## Browser / Playwright Screenshots

When taking screenshots, always save them to the `screenshots/` directory:

```
filename: "screenshots/<descriptive-name>.png"
```

`screenshots/` is listed in `.gitignore` and must never be committed. Never save screenshots to the project root or any other tracked location.

## GitHub Pages Setup

- The repository must have a `docs/CNAME` file containing `arc42AndLasr.marmer.online`.
- GitHub Pages source must be set to the `docs/` folder on the `main` (or `master`) branch.
- No build step is required for deployment; the generated files are committed directly.
