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

## Unified illustration style for supporting images — 2026-06-15

Many slides carry supporting images (concept icons, metaphor doodles, people
scenes) that today come from several different generators and clash stylistically
(flat teal+black outline icons, soft-3D gamepad, pale monochrome silhouettes,
one ink doodle). Decision: regenerate them in **one unified hand-drawn doodle
style**. Worked out interactively; locked spec below.

**In scope** (icon/metaphor/figure images only): slides 2, 3, 10, 11, 14–17,
19–28, 36, 50, 51, 52, plus the reused gamepad on 34/37/45/46/47 and the
document-with-magnifier icon. **Out of scope** (stay realistic): the product-
example screenshots on slide 36 (Netflix/DeepL/VPN/privacy/metrics), forms
(quality-criteria-form), document/UI content, and the LASR diagrams
(lasr-overview, utility-tree, radar) — these keep their "real-world / data" look.

Style spec:
- **Production**: AI raster images driven by a *locked* style prompt (generated
  externally — this repo/env has no image model; the generator only swaps the
  asset files). Anchor reference: the existing `questions-doodle`.
- **Technique**: hand-drawn marker/doodle.
- **Line**: variable-width brush-pen outline in near-black `#1B1B1B` (pressure
  taper + slight wobble) with light loose cross-hatching for shading.
- **Palette**: black line + exactly two accents — teal `#6CCBB2` (primary),
  sky-blue `#90C5E2` (secondary), plus light tints `#B6E5D9` / `#E0F4EF`.
  No other hues. White ground. (All drawn from the deck's existing palette.)
- **Carrier**: each subject sits on a slightly irregular torn-edge **white paper
  sticker with a soft drop shadow** (the `questions-doodle` treatment), unifying
  every motif.
- **Composition**: mixed — simple terms as a single centered object, richer
  statements as a small scene/vignette.
- **Figures**: simple gender-neutral doodle figures, minimal facial features
  (dot eyes, line mouth), never recognizable individuals; one consistent cast.
- **Integration**: layout may be lightly re-fitted per motif (not a strict 1:1
  footprint swap); a reused icon stays a single de-duplicated file so it remains
  pixel-identical across its slides (preserves the "no jumps between slides" rule).

**Locked master style prompt** (English, appended to every motif prompt):
> Hand-drawn doodle illustration. Variable-width brush-pen ink outline in
> near-black (#1B1B1B) with natural pressure taper and a slight hand-drawn
> wobble; light loose cross-hatching for shading. Flat color fills using ONLY
> teal #6CCBB2 (primary accent) and sky-blue #90C5E2 (secondary accent), plus
> their light tints #B6E5D9 / #E0F4EF for soft areas — no other hues. Subject
> rests on a slightly irregular, torn-edge white paper sticker with a soft drop
> shadow, like a sticker placed on the slide. People are simple, gender-neutral
> doodle figures with minimal facial features (dot eyes, small line mouth),
> never recognizable individuals. Friendly, playful, clean. Plain white
> background, subject centered with generous margin. No text or labels, no brand
> logos, no gradients, no photorealism.

**Process**: validate the style on one pilot motif first, then roll out the rest.
Pilot motif = the sleepy audience (slide 2):
> [master prompt] — Subject: a small audience of three or four simple doodle
> figures sitting in a row of chairs facing forward; one figure is yawning with
> closed eyes and a tiny "Zzz" floating above, the others looking bored —
> conveying a sleepy, unengaged audience during a talk.

### Regenerating
```bash
pip install -r scripts/requirements.txt
python3 scripts/pptx2reveal.py "arc42AndLasr_talk - envite_original.pptx" docs "arc42AndLasr_talk - envite_original_rendered.pdf"
python3 scripts/compare_render.py            # visual diff against the PDF
```
