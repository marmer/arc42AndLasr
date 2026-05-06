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
- [x] Slide 11: Warm Up – use proven methods; PPTX source = slide15.xml; main visual = inline SVG (replaces extracted slide11-image35.png); circle split blue-left / teal-right with tinted halves, teal ring, center divider; left icons: document, speech bubble, people (blue #3390C3); right icons: gear, </>, shield+checkmark (teal #6CCBB2); text labels "Business & Domain" / "Technical & Quality" outside ring; "Architecture & System Reviews" below as .arch-review-title; speaker notes from notesSlide12.xml (approaches not covered: Code Reviews, Event Storming, ATAM…)
- [x] Slide 12: Today is about — arc42 & LASR — PPTX slide 16; inline SVG pentagon diagram with 5 goals (Simplicity/Quality/Fun/Agility/Laziness); notes updated with translated PPTX notes + goal list
- [ ] Slide 13: [WIP] — PPTX slide 17; speaker notes transferred (arc42 intro: lightweight template by Starke & Hruschka); content pending
- [ ] Slide 14: [WIP] — PPTX slide 19; speaker notes transferred (arc42 ch.1: requirements & goals); content pending
- [ ] Slide 15: [WIP] — PPTX slide 20; speaker notes transferred (arc42 ch.2: constraints); content pending
- [ ] Slide 16: [WIP] — PPTX slide 21; speaker notes transferred (arc42 ch.3: context); content pending
- [ ] Slide 17: [WIP] — PPTX slide 22; speaker notes transferred (arc42 ch.4: solution strategy); content pending
- [ ] Slide 18: [WIP] — PPTX slide 23; speaker notes transferred (arc42 ch.5: building block / views); content pending
- [ ] Slide 19: [WIP] — PPTX slide 24; speaker notes transferred (arc42 ch.8: cross-cutting concepts); content pending
- [ ] Slide 20: [WIP] — PPTX slide 25; speaker notes transferred (arc42 ch.9: design decisions); content pending
- [ ] Slide 21: [WIP] — PPTX slide 26; speaker notes transferred (arc42 ch.10: quality requirements); content pending
- [ ] Slide 22: [WIP] — PPTX slide 27; speaker notes transferred (arc42 ch.11: risks & technical debt); content pending
- [ ] Slide 23: [WIP] — PPTX slide 28; speaker notes transferred (arc42 ch.12: glossary); content pending
- [ ] Slide 24: [WIP] — PPTX slide 29; speaker notes transferred (when & why to document with arc42); content pending
- [ ] Slide 25: [WIP] — PPTX slide 31; speaker notes transferred (transition to LASR section); content pending
- [ ] Slide 26: [WIP] — PPTX slide 32; speaker notes transferred (LASR intro: lightweight, gamified, agile-friendly); content pending
- [ ] Slide 27: [WIP] — PPTX slide 33; speaker notes transferred (LASR prerequisites: stakeholders, tools, budget, notes); content pending
- [ ] Slide 28: [WIP] — PPTX slide 34; speaker notes transferred (LASR prerequisites — repeated); content pending
- [ ] Slide 29: [WIP] — PPTX slide 35; speaker notes transferred (LASR core review vs. LASR+); content pending
- [ ] Slide 30: [WIP] — PPTX slide 36; speaker notes transferred (key features / USP); content pending
- [ ] Slide 31: [WIP] — PPTX slide 37; speaker notes transferred (LASR step: lean mission statement); content pending
- [ ] Slide 32: [WIP] — PPTX slide 38; speaker notes transferred (LASR step: lean mission statement — repeated); content pending
- [ ] Slide 33: [WIP] — PPTX slide 39; speaker notes transferred (LASR: fundamental requirements); content pending
- [ ] Slide 34: [WIP] — PPTX slide 40; speaker notes transferred (LASR: weighting goals); content pending
- [ ] Slide 35: [WIP] — PPTX slide 41; speaker notes transferred (LASR: requirements gap); content pending
- [ ] Slide 36: [WIP] — PPTX slide 42; speaker notes transferred (LASR: explore architecture); content pending
- [ ] Slide 37: [WIP] — PPTX slide 43; speaker notes transferred (LASR: points as percentage); content pending
- [ ] Slide 38: [WIP] — PPTX slide 44; speaker notes transferred (LASR: requirements gap — repeated); content pending
- [ ] Slide 39: [WIP] — PPTX slide 45; speaker notes transferred (LASR: define focus topic); content pending
- [ ] Slide 40: [WIP] — PPTX slide 46; speaker notes transferred (LASR: sharpen results); content pending
- [ ] Slide 41: [WIP] — PPTX slide 47; speaker notes transferred (LASR: visualization pro tip); content pending
- [ ] Slide 42: [WIP] — PPTX slide 48; speaker notes transferred (LASR: visualization pro tip — repeated); content pending
- [ ] Slide 43: [WIP] — PPTX slide 49; speaker notes transferred (LASR: visualization pro tip — repeated); content pending
- [ ] Slide 44: [WIP] — PPTX slide 50; speaker notes transferred (LASR: quality scenarios / NFRs); content pending
- [ ] Slide 45: [WIP] — PPTX slide 51; speaker notes transferred (LASR: bottom-up vs top-down analysis); content pending
- [ ] Slide 46: [WIP] — PPTX slide 52; speaker notes transferred (LASR: bottom-up vs top-down — repeated); content pending
- [ ] Slide 47: [WIP] — PPTX slide 53; speaker notes transferred (LASR: bottom-up vs top-down — repeated); content pending
- [ ] Slide 48: [WIP] — PPTX slide 54; speaker notes transferred (LASR: derive next steps & communicate); content pending
- [ ] Slide 49: [WIP] — PPTX slide 55; speaker notes transferred (outcome: document what you learned); content pending
- [ ] Slide 50: [WIP] — PPTX slide 56; no speaker notes; content pending
- [ ] Slide 51: [WIP] — PPTX slide 57; speaker notes transferred (call to action: ask, analyze, document); content pending
- [ ] Slide 52: [WIP] — PPTX slide 58; speaker notes transferred (contact / Q&A); content pending
- [ ] Slide 53: [WIP] — PPTX slide 59; no speaker notes; content pending
