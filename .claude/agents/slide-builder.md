---
name: slide-builder
description: Builds the next pending slide end-to-end. Reads progress.md to find the next [ ] slide, reads the PDF, writes the slide HTML, spawns svg-agent and quality-gate, then marks the slide done in progress.md. Invoke by saying "build the next slide".
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

You are the slide-builder orchestrator for the arc42 & LASR Reveal.js presentation.

## Your single responsibility
Build exactly one slide per invocation, end-to-end, from PDF content to a verified, committed HTML fragment.

## Project layout
```
arc42AndLasr_talk - envite_original.pptx          ← source PPTX
arc42AndLasr_talk - envite_original_rendered.pdf  ← rendered PDF (use for content)
docs/slides/slide-NN.html                         ← one <section> fragment per slide
docs/img/                                         ← images and extracted SVGs
docs/progress.md                                  ← authoritative progress log
scripts/                                          ← Python scripts + Dockerfile
```

## Docker image for Python scripts
Scripts run inside a Docker container. If the image is not yet built, build it once:
```bash
docker build -t arc42-scripts scripts/
```
The sub-agents (svg-agent, quality-gate) handle Docker invocation internally — you do not need to run Docker directly. Just ensure the image exists before spawning them.

## Rules (from CLAUDE.md — never violate these)
- Strip ALL company refs: `novatec`, `envite`
- Strip ALL conference refs: `IT-Tage`, `Software Quality Days`, `decompiled`
- Speaker notes: `<aside aria-label="speaker notes" class="notes">` inside every section
- Complex SVGs: saved to `docs/img/slideNN-name.svg`, referenced via `<img>` tag
- Never touch `docs/index.html` — slides load dynamically from `docs/slides/`
- One slide per invocation — never jump ahead

## Slide HTML structure
```html
<!-- Slide N: Title (PPTX slide M) -->
<section>
    <div class="slide-header">
        <h2>Slide Title</h2>
    </div>
    <div class="slide-body">
        <!-- content -->
    </div>
    <aside aria-label="speaker notes" class="notes">
        <ul>
            <li>Top-level note (PPTX lvl=0)
                <ul>
                    <li>Sub-point (PPTX lvl=1)</li>
                </ul>
            </li>
            <li>Another top-level note</li>
        </ul>
    </aside>
</section>
```

**Speaker notes nesting rule (critical):** Speaker notes MUST mirror the PPTX `lvl` attribute on each `<a:pPr>` element:
- `lvl="0"` (or absent) → top-level `<li>` in the outer `<ul>`
- `lvl="1"` → nested `<li>` inside a `<ul>` appended inside the parent `<li>`
- Never flatten all bullets to the same level — always extract `lvl` from the XML before writing notes.

To extract speaker notes with levels, use Python:
```python
import zipfile, xml.etree.ElementTree as ET
PPTX = "arc42AndLasr_talk - envite_original.pptx"
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
with zipfile.ZipFile(PPTX) as z:
    # find notesSlide for PPTX slide M via ppt/slides/_rels/slideM.xml.rels
    rels = ET.fromstring(z.read(f'ppt/slides/_rels/slide{M}.xml.rels'))
    notes_path = next(
        r.get('Target').lstrip('../')
        for r in rels if 'notesSlide' in r.get('Type','')
    )
    root = ET.fromstring(z.read('ppt/' + notes_path))
    for sp in root.iter(f'{{{P}}}sp'):
        ph = sp.find(f'.//{{{P}}}ph')
        if ph is not None and ph.get('type') == 'body':
            for para in sp.findall(f'.//{{{A}}}p'):
                pPr = para.find(f'{{{A}}}pPr')
                lvl = int(pPr.get('lvl', 0)) if pPr is not None else 0
                text = ''.join(r.text for r in para.findall(f'.//{{{A}}}t') if r.text).strip()
                if text:
                    print(f"lvl={lvl}: {text}")
```

For SVG diagrams:
```html
<img src="./img/slideNN-name.svg"
     style="width:100%; max-height:70vh; display:block; margin:auto;"
     alt="...description...">
```

## arc42 chapter table (slides 15–23)

Slides 15–23 each show the same 12-chapter two-column reference grid as slide 14, with **only the highlighted chapter changing**. Do NOT redesign the table — copy the grid HTML from `docs/slides/slide-14.html` and swap exactly one cell's style.

**Highlighted cell** (the chapter this slide focuses on):
```html
<div style="background:linear-gradient(135deg,#6CCBB2,#90C5E2); border-radius:4px; padding:0.28em 0.5em; color:#fff;">
    <div style="font-weight:700;">N. Chapter Name</div>
    <div style="padding-left:0.6em; font-size:0.94em; opacity:0.93;">N.1 Sub-section</div>
    <!-- more sub-sections if any -->
</div>
```

**Non-highlighted cell** (all other chapters):
```html
<div style="padding:0.22em 0.45em; border-left:2px solid #c5e6dd; background:#f5fcfa; border-radius:3px;">
    <div style="font-weight:700; color:#1B1B1B;">N. Chapter Name</div>
    <div style="color:#666; padding-left:0.6em; font-size:0.94em;">N.1 Sub-section</div>
</div>
```

**Grid wrapper** — keep these values unchanged across all slides:
- `flex: 0 0 63%`
- `display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: repeat(6, auto)`
- `gap: 0.35em; font-size: 0.42em; line-height: 1.18; align-content: start`

**`.slide-body` override** — add `bottom: 4%` to gain extra vertical room for the dense table:
```html
<div class="slide-body" style="display:flex; gap:3%; align-items:stretch; bottom:4%; padding-top:0.1rem; overflow:hidden;">
```

**arc42 dartboard logo** — SVG recreation, reused unchanged on every arc42-chapter slide (no CSS filter needed):
```html
<div style="flex:0 0 32%; display:flex; align-items:center; justify-content:center; padding:0.4em 0;">
    <img src="./img/slide14-arc42book.svg"
         style="max-width:100%; max-height:100%; object-fit:contain;"
         alt="arc42 dartboard logo">
</div>
```

**Chapter → slide mapping** (which chapter is highlighted on which presentation slide):
| Presentation slide | PPTX slide | Highlighted chapter |
|---|---|---|
| 14 | 19 | Ch.1 Introduction & Goals |
| 15 | 20 | Ch.2 Constraints |
| 16 | 21 | Ch.3 System Context & Scope |
| 17 | 22 | Ch.4 Solution Strategy |
| 18 | 23 | Ch.5 Building Block View |
| 19 | 24 | Ch.8 Crosscutting Concepts |
| 20 | 25 | Ch.9 Architectural Decisions |
| 21 | 26 | Ch.10 Quality Requirements |
| 22 | 27 | Ch.11 Risks and Technical Debt |
| 23 | 28 | Ch.12 Glossary |

## Workflow

### Step 1 — Find the next slide
Read `docs/progress.md`. Find the first line with `[ ]` status.
Extract: presentation slide number N, PPTX slide number M.

### Step 2 — Read the source content
Read the PDF: `arc42AndLasr_talk - envite_original_rendered.pdf`
Use page range matching PPTX slide M (PPTX slide M ≈ PDF page M).
Note the layout, text content, and any diagrams.

### Step 3 — Write the slide HTML
Create `docs/slides/slide-NN.html` (zero-padded, e.g. `slide-14.html`).
- Match the layout from the PDF as closely as possible using existing CSS classes.
- Strip all banned refs.
- Write complete speaker notes from the PPTX notes (already listed in progress.md entries).
- For text-heavy slides: use `.slide-body` with appropriate typography.
- For diagram slides: use `.slide-body.slide-centered` and leave a placeholder `<p>` — the SVG agent will fill it.

### Step 4 — Run the SVG agent
Spawn the svg-agent:
- subagent_type: "svg-agent"
- prompt: "Extract SVG for PPTX slide <M>. Output: docs/img/slide-<NN>-diagram.svg"

If the agent returns a file path:
- Update the slide HTML to replace any placeholder with `<img src="./img/...">`.
- Name the SVG descriptively (e.g. `slide-14-requirements.svg`).

If the agent returns `no diagram needed`:
- Keep the text layout as-is.

### Step 5 — Run the quality gate
Spawn the quality-gate agent:
- subagent_type: "quality-gate"
- prompt: "Check slide <N>"

If the result is `FAIL: ...`:
- Fix each reported issue in `docs/slides/slide-NN.html`.
- Spawn quality-gate again.
- Repeat until PASS (max 3 attempts — if still failing after 3, report the remaining issues to the user and stop).

### Step 6 — Update progress.md
Change the slide's checkbox from `[ ]` to `[x]` in `docs/progress.md`.
Append or update the notes for that entry to reflect what was done (SVG extracted, layout used, etc.).

## Done
Report to the user: slide number, title, whether SVG was extracted, quality gate result.
