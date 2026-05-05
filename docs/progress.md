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
- [x] Slide 4: Warm Up — section intro; PPTX source = slide8.xml; full title "Warm Up – What can possibly happen?" in header; body empty (matches original "Inhalt Leer" layout); speaker notes translated from notesSlide5.xml
- [x] Slide 5: Warm Up case 1 — COBOL / NY unemployment; PPTX source = slide9.xml; same header title as slide 4; CNN article image (slide4-warmup-img.png) rotated -11.6° with drop shadow; speaker notes from notesSlide6.xml
- [x] Slide 6: Warm Up case 2 — Healthcare.gov; PPTX source = slide10.xml; two overlapping images: COBOL (warmup-img-1, -11.6°) + Healthcare.gov Medium article (slide6-case2.png, warmup-img-2, -17.9°); absolutely positioned collage; speaker notes from notesSlide7.xml
- [x] Slide 7: Warm Up case 3 — BBC "US prisoners released early by software bug"; PPTX source = slide11.xml; adds warmup-img-3 (image31.png, -22.6°); speaker notes from notesSlide8.xml
- [x] Slide 8: Warm Up case 4 — Wired "Software Glitch Cripples Ambulance Service"; PPTX source = slide12.xml; adds warmup-img-4 (image32.png, -30.9°); closing question "what do all cases have in common?"; speaker notes from notesSlide9.xml
- [x] Slide 9: Warm Up — further collection; PPTX source = slide13.xml; adds warmup-img-5 (image33.png, "Humans vs Computers" book cover by Gojko Adzic, no rotation, portrait); speaker notes from notesSlide10.xml
- [x] Slide 10: Warm Up – Now what?; PPTX source = slide14.xml; single centered question-mark icon (image34.png → slide10-image34.png); .slide-body.slide-centered; two note groups (can't prevent everything / key questions); speaker notes from notesSlide11.xml
- [x] Slide 11: Warm Up – use proven methods; PPTX source = slide15.xml; main visual = slide11-image35.png (circular blue/green diagram); text labels "Business & Domain" / "Technical & Quality" / "Architecture & System Reviews" rendered in HTML below the image; .arch-review-diagram CSS added to custom.css; speaker notes translated from German
