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

## Unified SVG image style — decisions (2026-07-02)

Interview-driven style definition for regenerating the supporting images as
SVGs (affected slides, new deck numbering: 2, 3, 10, 11, 14–17, 19–28, 36,
50, 51, 52 (badge only) + the gamepad on 34, 37, 45 (incl. document with
magnifier), 46, 47). All decisions confirmed with the author:

- **Base style**: duotone line style — uniform #1B1B1B outline (~3.5 units on
  a 100-unit viewBox, round caps/joins), flat fills, no shadows/gradients,
  geometric construction, shared grid. Everything must stay legible at the
  smallest on-slide render size (~100px).
- **Color rule**: fills limited to mint #6CCBB2, pale mint #B2E4D7 and white;
  amber #F4AD0E reserved for exactly one attention element per image (where
  meaningful). Blues (#3390C3/#90C5E2) are reserved for the "THAT'S IT
  FOLKS" rings, which keep the Looney-Tunes homage (incl. text, set in
  DM Sans 700 as real SVG text) as the single deliberate escape from the
  mint rule. Grey ring variant derived for slides 25/51.
- **Motifs stay, style changes**: every image keeps its current motif and its
  exact bounding box/aspect ratio (no layout shifts). The three gamepad PNG
  variants collapse into ONE gamepad SVG used on all gamepad slides (the
  color differences carried no meaning; the mini LASR map already marks the
  active step). Slide 51: only the grey rings + the analyze/evaluate/improve
  cycle are redrawn; book covers and iSAQB logo remain untouched (real
  third-party artifacts). Slide 52: only the feedback badge is redrawn (the
  same badge motif as slide 3); the LinkedIn QR stays as-is (functional).
- **Animation**: subtle infinite loops only ("living stills"), 4–8s,
  max 1–2 animated elements per image, staying static is allowed;
  `prefers-reduced-motion` disables all loops. No entrance/draw-in
  animations (they fight Reveal fragments and re-entry).
- **Integration**: SVGs are hand-maintained source files in `assets/svg/`;
  the generator gets a replacement table (original media → SVG file) and
  inlines the SVG content into the slide HTML (like `_title_bg_svg`), so the
  self-hosted webfonts and CSS animations apply. All ids/classes inside each
  SVG carry a per-image prefix to avoid collisions once inlined.
- **Verification**: `compare_render.py` gets an auto-derived mask list
  (slide → rectangles of replaced images) excluded from the diff, so RMS
  stays meaningful for text/layout; the new images themselves are reviewed
  visually.
- **Process**: style tile first (`assets/svg/preview.html`, built by
  `assets/svg/build_preview.py`, self-contained with embedded fonts) with 5
  representative samples: gear-warning, yawning-person, target-dartboard,
  gamepad, thats-it-folks-rings. Mass production of the remaining images
  only after the style tile is approved.

## Unified SVG images — round 2: full production (2026-07-02)

All ~20 images produced in `assets/svg/` (style approved via the round-1
style tile) and wired into the pipeline:

- `pptx2reveal.py`: `SVG_REPLACEMENTS` maps final `docs/img` names to the
  SVG sources; `inline_svg()` embeds them into the slide HTML in place of
  the `<img>` (wrapper carries `data-svg-replaced`). The padded PDF-extract
  canvases (grey/color rings) are handled by a fit-box that nests the
  artwork at the original content position. PPTX picture drop-shadows are
  stripped on replaced images (flat style bans shadows). The replaced PNGs
  are no longer written to `docs/img/`.
- `DROPPED_SLIDES`: slide59 (duplicate closing slide the author had removed
  by hand in commit "Last slide removed") is now skipped by the generator —
  previously a regeneration would have resurrected it.
- `compare_render.py` masks the `data-svg-replaced` regions (queried from
  the live DOM) out of the RMS diff, so the score stays meaningful for
  text/layout; composites show the real render but diff the masked images.
- Animations: CSS keyframes/offset-path only. SMIL does not start inside the
  fetch-injected slide files (the title slide, injected the same way, is the
  lone exception that works) — the cycle-diagram orbit dot therefore uses
  CSS `offset-path`. All animations respect `prefers-reduced-motion`.
- Verified: full `compare_render.py` run + visual review of all 27 affected
  slides; CSS + title SMIL animations confirmed live in headless Chromium.
- Known intended deviations vs the PDF: the replaced images themselves
  (masked), and slide 52's RMS is 0 because the full-slide badge region is
  masked entirely.

## Ink highlights (slide 32) + SVG icon fit boxes (slide 45) — 2026-07-04

- Slide 32 (pptx slide38): the yellow marker highlights on the Threema quote
  are PowerPoint ink (`p:contentPart` wrapped in `mc:AlternateContent`) —
  the generator skipped those elements, so the highlights were missing.
  `walk_shape` now descends into `mc:Fallback` and renders the pre-rendered
  ink bitmaps (media slugs `marker-*`). Highlighter ink (InkML brush
  `rasterOp=maskPen`) is rendered with `mix-blend-mode:multiply` so the text
  stays readable through the marker, matching PowerPoint's blend.
- The same mechanism surfaced ink on pptx slides 7/58: the smiley face drawn
  onto the original alien badge artwork. That artwork is redesigned
  (hello-badge.svg / feedback-badge.svg) without the alien, so those four
  strokes are intentionally skipped (`SKIPPED_INK_MEDIA`).
- Slide 45: the document-magnifier and gamepad SVG replacements overlapped —
  the padded PDF-extract canvases (artwork fills only ~half the bitmap) were
  filled edge-to-edge by the SVGs. gamepad, warning-electric and
  document-magnifier now carry fit boxes (square sub-viewports that
  compensate both the bitmap padding and the SVG's own viewBox margins),
  restoring the original on-slide artwork size/position. Affected slides
  (new numbering): 26, 34, 36, 37, 45, 46, 47 — all verified via
  `compare_render.py` composites.

## Slide 2 icon size + unified gamepad position (2026-07-04)

- Slide 2: gear-warning and yawning-person rendered ~15% larger than the
  PPTX (their raster originals carry transparent margins the SVGs lack) —
  both now have fit boxes derived from the bitmaps' alpha bounding boxes.
- Gamepad marker: the original deck places the "workshop game" gamepad at a
  different spot on every game slide — mid-left on slide 45, half inside
  the title bar on 46/47, below the title bar on 34/37. On the author's
  request the gamepad on 45/46 (and 47, which shares 46's layout — keeping
  the no-jump rule between consecutive slides) is pinned to the 34/37
  position via `PIC_POS_OVERRIDES` (a deliberate deviation from the PPTX).

## Gamepad revert (slide 45), title z-order (slide 51), slide1 hand edits (2026-07-04)

- Slide 45: the gamepad override from the previous change is reverted on the
  author's request — it stays at its PPTX position next to the "Top Down"
  bullet. Slides 46/47 keep the pinned 34/37 position.
- Slide 51: the closing title "Start doing and keep on learning!" hides
  behind the "THAT'S IT FOLKS" rings in the original PPTX; a new
  `SHAPE_Z_OVERRIDES` table lifts it above the artwork (same position).
- The author's hand edits to the generated slide1.html (commits "Revise
  slide content and layout in slide1.html" / "Change author description in
  slide1.html": bio now "Software- and Solution-Architect, Trainer, Father,
  Nerd") are ported into `TEXT_REPLACEMENTS` (anchored to the exact run
  texts) so regeneration no longer reverts them. Slide files are now
  written with a trailing newline (one-time churn across all slides) so
  editor-saved files stay diff-stable.
