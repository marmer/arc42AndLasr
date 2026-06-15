# arc42 & LASR Talk — Slide Progress

## Rebuild (from-scratch conversion) — 2026-06-11

The first conversion attempt (hand-written slide HTML in `docs/slides/`) was
removed. The presentation is now **generated** from the original PPTX by
`scripts/pptx2reveal.py`:

- DrawingML shape coordinates (EMU) are translated directly into absolutely
  positioned HTML on a 960×540 canvas. Identical shapes therefore land on
  identical pixels across slides — no visual jumps between consecutive slides
  or animation steps (verified programmatically; the only three sub-25px
  shifts that exist are present in the original PPTX as well).
- Text styles are resolved through the full inheritance chain
  (run → paragraph → shape lstStyle → layout placeholder → master placeholder
  → master txStyles → presentation default → theme), including
  normAutofit fontScale, anchor, insets, bullets and autonumbering.
- PowerPoint entrance animations (`p:timing`) become Reveal.js fragments:
  one fragment index per click group; afterEffect chains inside a single
  click are reproduced with staggered CSS transition delays.
- SmartArt (slide "Today is about") is rendered from the pre-laid-out
  diagram drawing part (`ppt/diagrams/drawing1.xml`).
- Pictures with PowerPoint backgroundRemoval (~65 of them) cannot be
  recomputed, so the processed bitmaps (incl. baked duotone) are extracted
  from the original rendered PDF by position matching.
- Tables, connectors (incl. arrowheads), curly braces, custom geometry,
  gradient fills/strokes, pattern-filled WordArt, rotation/flips and grouped
  shapes (incl. rotated groups) are all handled by the generator.
- Fonts: DM Sans + Karla are self-hosted in `docs/fonts/` (woff2).
  Letter-spacing is calibrated (−0.012em) because the webfonts run ~1–2%
  wider than PowerPoint's rasterizer; this makes tightly autofitted titles
  wrap exactly like the original.
- Speaker notes are extracted from the notes slides (nested lists).
- Image files in `docs/img/` get **descriptive names** (e.g.
  `lasr-plus-radar.png`, `gamepad-icon.png`, `closing-background.jpeg`) via the
  `MEDIA_SLUGS` (source media) and `PDF_SLUGS` (PDF-extracted icons) tables at
  the top of the generator. Identical content is de-duplicated to one file, so
  an icon reused across slides keeps a single name; the rare distinct image
  sharing a slug gets a `-2`/`-3` suffix.

### Company/conference reference removal
- envite logo (`ppt/media/image2.png`) blacklisted everywhere.
- Title-slide background photo (`ppt/media/image3.jpeg`) was an employer-branded
  landscape. `render_pic` special-cases it and emits an **inline animated SVG**
  (`_title_bg_svg`): a license-free, procedurally drawn golden-hour ridgeline
  (sky/sun/foreground gradients + ridge paths) with two stick figures tossing a
  ball back and forth (SMIL `animateMotion` on a there-and-back arc); each
  figure's throwing arm swings up in sync as the ball reaches its hand. Inline so
  the animation runs (it would not in an `<img>`-referenced SVG). No raster
  `title-background.*` file is produced anymore.
  NOTE: the closing-slide background (`image1.jpeg`, a turquoise-river photo) is
  likely also employer imagery — left unchanged for now, replace on request.
- Tagline "Pioneering IT Sustainability" and all envite/novatec/IT-Tage/
  decompiled/Software Quality Days texts filtered (slides + notes).
- Contact slide: `…@envite.de` → `mariano.mertinat@gmail.com`, personal phone
  number dropped, vCard QR code regenerated without employer data
  (name, title, gmail, https://marmer.online).
- The sli.do event QR only appears on a hidden slide and is not exported.

### Verification
`scripts/compare_render.py` screenshots every slide (headless Chromium,
960×540, final fragment state) and diffs it against the page of the original
PowerPoint-rendered PDF; composites land in `screenshots/compare/`.

Remaining known deviations (accepted):
- Slides 1 and 53: PowerPoint's PDF **export** flattens the white
  alpha-gradient overlay to near-solid white; on screen PowerPoint (and
  LibreOffice, pixel-identical to our render) shows the photo through the
  gradient like our version does.
- Dense 8pt-text slides (arc42 template family) show only rasterizer-level
  text antialiasing differences.

### Slide status (53 visible slides; hidden PPTX slides 2, 3, 4, 6, 18, 30 skipped)
All 53 slides generated and visually verified against the reference PDF:
- [x] 1–53: generated, references removed, notes attached, fragments mapped
      (multi-click: slide 31; single-click stagger groups: 26, 29, 30, 34,
      37, 45, 46, 47, 51)

### Regenerating
```bash
pip install -r scripts/requirements.txt
python3 scripts/pptx2reveal.py "arc42AndLasr_talk - envite_original.pptx" docs "arc42AndLasr_talk - envite_original_rendered.pdf"
python3 scripts/compare_render.py            # visual diff against the PDF
```
