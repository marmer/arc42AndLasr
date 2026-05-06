# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Convert the arc42 + LASR conference talk (originally in `arc42AndLasr_talk - envite_original.pptx` / `.pdf`) into a **Reveal.js presentation** hosted as a GitHub Page at **arc42AndLasr.marmer.online**.

Key constraints:
- **No company references**: remove all mentions of novatec, envite, or any employer.
- **No specific conference references**: remove IT-Tage, Software Quality Days, decompiled, or any named event.
- Work is done **one slide at a time** — never jump ahead.
- Track progress in `docs/progress.md` (see below).

## Project Structure

```
docs/               ← GitHub Pages root (serves index.html)
  index.html        ← main presentation (all slides live here)
  dist/             ← reveal.js compiled assets (reset.css, reveal.css, reveal.js)
  plugin/           ← reveal.js plugins (highlight, notes, markdown, search, zoom, charts, countdown, reveal-plantuml)
  css/
    custom.css      ← custom styles (gradient headings, layout helpers, etc.)
  img/              ← slide images extracted from the original PPTX
  js/               ← custom JS (e.g. chart data)
  CNAME             ← arc42AndLasr.marmer.online
  progress.md       ← slide-by-slide progress log (source of truth across sessions)
```

The tdd-workshop sibling project (`../tdd-workshop/docs/`) is the structural reference. Copy its `dist/`, `plugin/`, and `package.json` as the starting point; do **not** copy company-branded CSS or unused plugins.

## Development Commands

```bash
# install dependencies (run once inside docs/)
npm install

# local dev server with live reload
npm start           # runs: gulp serve  → http://localhost:8000

# build (compiles SCSS themes, minifies JS)
npm run build       # runs: gulp build
```

No test command is needed for the presentation itself; browser inspection is the verification step.

## Reveal.js Conventions (match the reference project)

- **Reveal.initialize config**: `hash: true`, `slideNumber: "c/t"`, `history: true`, `mouseWheel: true`, `transition: 'fade'`, `navigationMode: "linear"`.
- **Section structure**: top-level `<section>` = horizontal slide; nested `<section>` = vertical sub-slide.
- **Speaker notes**: `<aside aria-label="speaker notes" class="notes">` inside each section.
- **Background image**: `data-background-image` / `data-background-opacity` attributes on sections.
- **Animation**: `data-auto-animate` on adjacent sections triggers auto-animate transitions.
- **Slide images**: exported from the PPTX and stored in `docs/img/`. Reference as `./img/<file>`.
- **Plugins loaded**: RevealMarkdown, RevealHighlight, RevealNotes, RevealSearch, RevealZoom. Extra plugins (Charts, Countdown, PlantUML) loaded via `dependencies`.

## Progress Tracking

`docs/progress.md` is the authoritative log. At the start of every session, read it to know where to continue. After completing a slide, append an entry:

```markdown
## Slide <N>: <Title>
- Status: done
- Notes: <anything worth remembering about decisions made>
```

When starting a new session without a progress file, create it first before touching `index.html`.

## Workflow for Each Slide

1. Read `docs/progress.md` to find the next slide to work on.
2. Read the corresponding page(s) in the rendered PDF (`arc42AndLasr_talk - envite_original_rendered.pdf` for layout and content.
3. Extract / create content in `index.html` — one `<section>` at a time.
4. Strip any company/conference references.
5. Add speaker notes from the original where available (from arc42AndLasr_talk - envite_original.pptx).
6. Update `docs/progress.md`.

## Browser / Playwright Screenshots

When taking screenshots with the Playwright MCP tool, always save them to the `screenshots/` directory:

```
filename: "screenshots/<descriptive-name>.png"
```

`screenshots/` is listed in `.gitignore` and must never be committed. Never save screenshots to the project root or any other tracked location.

## GitHub Pages Setup

- The repository must have a `docs/CNAME` file containing `arc42AndLasr.marmer.online`.
- GitHub Pages source must be set to the `docs/` folder on the `main` (or `master`) branch.
- No build step is required for deployment; the compiled `dist/` and `plugin/` files are committed directly (same pattern as tdd-workshop).
