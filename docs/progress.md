# arc42 & LASR Talk — Slide Progress

## Status legend
- `[ ]` pending
- `[~]` in progress
- `[x]` done

## Layout / Theme Work

### 2026-05-04 — Default layout redesign
- Analysed original PPTX: light/white theme, DM Sans Bold headings, Karla body
- Colors: bg #FFFFFF, header bar #E8E8E8, text #1B1B1B, teal accent #6CCBB2
- Replaced `black.css` → `white.css` Reveal.js theme
- Added Google Fonts: DM Sans + Karla
- Rewrote `custom.css` to match original slide master layout:
  - `.slide-title`: title slide with photo on right, white gradient overlay, positioned text
  - `.slide-header` + `.slide-body`: content slides with gray header bar, teal gradient underline
  - Fixed teal bottom-right accent line (`.slide-footer-accent`)
- Extracted `title-bg.jpeg` (river/forest photo) → `docs/img/`
- Company logo (envite) removed per CLAUDE.md policy

## Slides

- [x] Slide 1: Title — layout redesigned to match original; speaker notes + teal accent verified
- [x] Slide 2: Who is this talk for? — two-photo layout (slide2-who-left.png / slide2-who-right.png from PPTX image21/22); standard slide-header + slide-two-photos CSS; speaker notes translated from German; PPTX source = slide5.xml (slide5 is visible; slide6 hidden/alternate variant ignored)
- [x] Slide 3: Who am I? — Speaker introduction + LinkedIn QR code; PPTX source = slide7.xml; badge redrawn in HTML/CSS (`.hello-badge`); photo = MertinatMariano_1000x1000_web_transparent_head_only.png; QR code generated for marmer.online; speaker notes from notesSlide4.xml ("At work nearly 14 years…")
