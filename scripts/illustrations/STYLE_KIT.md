# Illustration style kit — read this before drawing any motif

All supporting icons / metaphors / figures in the deck are hand-authored inline
SVG in **one** unified doodle style. The generator (`pptx2reveal.py`) inlines
`scripts/illustrations/<slug>.svg` in place of the original raster
`<img src="img/<slug>.png">`. Drop a `<slug>.svg` here and it is used
automatically — no other wiring.

## Hard rules (consistency depends on these)

1. **File = one standalone `<svg>`** with `viewBox="0 0 300 300"`
   `preserveAspectRatio="xMidYMid meet"` and **no** `width`/`height` attrs
   (the generator sizes it to the slide footprint).
2. **Copy the shared `<defs>` block verbatim** (below). Keep the ids
   `rough`, `shadow`, `hatch` exactly — the generator namespaces them per
   slide so they never collide.
3. **Palette — only these colors:**
   - ink line `#1b1b1b`
   - teal (primary) `#6CCBB2`, blue (secondary) `#90C5E2`
   - light tints `#B6E5D9`, `#E0F4EF`
   - white `#ffffff`
   No other hues, no gradients.
4. **Line:** `stroke="#1b1b1b"`, `stroke-width="3"` (small details `2.2`),
   `stroke-linecap="round"`, `stroke-linejoin="round"`, `fill="none"` for
   outlines. Put all line art in one `<g id="artwork" filter="url(#rough)">`
   so strokes + fills wobble together (the hand-drawn look).
5. **Sticker:** every motif sits on the torn-paper white sticker (the
   `<g filter="url(#shadow)">` block below). Reshape its path to roughly the
   motif's bounding box if needed, but keep the white fill + soft shadow.
6. **Shading:** use the `url(#hatch)` pattern (a `<path>`/shape with
   `fill="url(#hatch)" stroke="none"`) for light cross-hatch shadow on the
   shaded side. Keep it sparse.
7. **Figures:** simple, gender-neutral doodle people — round head, dot/short
   features, no recognizable individuals. Reuse the body/head proportions from
   the pilot so the cast looks like one family.
8. **Animation:** one *very subtle* idle loop (long `dur`, tiny amplitude,
   `calcMode="spline"` ease). E.g. gentle bob (≤1.5px), slow sway (≤2°), a slow
   blink, a drifting "Zzz". Use SMIL (`<animate>` / `<animateTransform>`).
   Never large or attention-grabbing. A motif with no natural motion may use
   only the whole-artwork bob, or none.
9. **No text, no logos, no company/conference references.**

## Shared defs (copy verbatim)

```xml
<defs>
  <filter id="rough" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.014" numOctaves="2" seed="7" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="2.6" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#1b1b1b" flood-opacity="0.16"/>
  </filter>
  <pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="8" stroke="#1b1b1b" stroke-width="1" opacity="0.22"/>
  </pattern>
</defs>
```

## Reference example

`yawning-person-icon.svg` (the approved pilot) is the canonical example of all
the rules above — read it before drawing.

## How to preview a motif

```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers playwright screenshot \
  --browser chromium --viewport-size 340,340 \
  "file://$PWD/scripts/illustrations/<slug>.svg" screenshots/<slug>.png
```
(SVGs render directly in the browser; or regenerate the deck and screenshot the
slide.)
