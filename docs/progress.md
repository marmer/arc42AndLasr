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

## Icon restyle — flat duotone SVGs — 2026-06-23

The standalone pictogram artwork (the stock-looking icons originally extracted
from the PDF or baked into the PPTX) was replaced with a single coherent set of
hand-drawn flat icons. Goal: one consistent visual language, licence-clean
artwork, crisp at any zoom, and removal of the copyrighted Looney Tunes
"That's all folks" rings.

**Locked style** (signed off via a 3-icon pilot — gamepad, audience,
document+magnifier):
- Flat duotone, *outlined + filled*: uniform dark-ink keyline around flat
  teal fills, rounded joins/caps, one normalised stroke weight per icon
  (`stroke-width: 4` on a 100-unit viewBox; finer detail uses ~1.8–3).
- Palette: ink `#1B1B1B`, brand teal `#6CCBB2`, light teal `#E0F4EF`, white
  knockout. `#FF0000` reserved for genuine warning subjects only (none used —
  the gear/electric warnings stay on-brand teal).
- Transparent, shadowless (the generator drops the `drop-shadow` filter for
  `.svg` icons), sized to the exact box of the image they replace → no
  composition shift.
- **Selective** subtle idle animation, only where the subject implies motion
  (gears rotate, network/checks pulse, paper whirls, magnifiers scan, runner
  bobs, bolt flickers, arrows breathe, iris pulses); the rest are static
  (person, chess knight, target, feather sways gently). Each animation is a
  CSS `@keyframes` embedded inside the SVG with an internal
  `@media (prefers-reduced-motion: reduce)` off-switch.
- Gamepad: a minimal retro rectangular pad was chosen over a dual-grip / rounded
  variant.

**Mechanism**: sources live in `scripts/icons/<slug>.svg`. The generator
(`icon_svg()` + `ICON_SVGS`/`ICON_ALIASES`) swaps them in for both the
PDF-extracted (`extract_from_pdf`) and duotone-`emit_media` paths, keyed by the
slug each original would have produced. Colour/state variants of one subject
(e.g. the three ring treatments) alias onto a single drawing.

**Restyled (19 drawings)**: gamepad, audience-people, document-magnifier,
target-dartboard, gears-lock, circuit-network, checklist-gear, circuit-checks,
paper-whirl, book-magnifier, feather, person-suit, running-person,
warning-electric, chess-knight, arrows-outward, gear-warning, yawning-person,
thats-it-folks-rings (replaces the colour/grey/grey-faded ring variants).

**Deliberately excluded**: `sharpen-results-checklist` (image68) is not a
pictogram but a full content graphic with real text ("Quality Statement", the
question prompts, the "Performance Efficiency" card) — left as-is.

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
