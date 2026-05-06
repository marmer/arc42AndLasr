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
- [~] Slide 12: arc42 & LASR — PPTX slide 16; content implemented: 5 arc42 goals (Simplicity/Quality/Agility/Fun/Laziness) as teal badge list; WIP ribbon
- [~] Slide 13: What is arc42 — PPTX slide 17; content: 4-aspect card layout (Template/Method/Philosophy/Cheat-Sheet); WIP ribbon
- [~] Slide 14: arc42 Template ch.1 — PPTX slide 19; content: arc42 12-chapter grid, ch.1 highlighted in teal; WIP ribbon
- [~] Slide 15: arc42 Template ch.2 — PPTX slide 20; content: arc42 grid, ch.2 highlighted; WIP ribbon
- [~] Slide 16: arc42 Template ch.3 — PPTX slide 21; content: arc42 grid, ch.3 highlighted; WIP ribbon
- [~] Slide 17: arc42 Template ch.4 — PPTX slide 22; content: arc42 grid, ch.4 highlighted; WIP ribbon
- [~] Slide 18: arc42 Template ch.5/6/7 — PPTX slide 23; content: arc42 grid, views ch.5-7 highlighted; WIP ribbon
- [~] Slide 19: arc42 Template ch.8 — PPTX slide 24; content: arc42 grid, ch.8 highlighted; WIP ribbon
- [~] Slide 20: arc42 Template ch.9 — PPTX slide 25; content: arc42 grid, ch.9 highlighted; WIP ribbon
- [~] Slide 21: arc42 Template ch.10 — PPTX slide 26; content: arc42 grid, ch.10 highlighted; WIP ribbon
- [~] Slide 22: arc42 Template ch.11 — PPTX slide 27; content: arc42 grid, ch.11 highlighted; WIP ribbon
- [~] Slide 23: arc42 Template ch.12 — PPTX slide 28; content: arc42 grid, ch.12 highlighted; WIP ribbon
- [~] Slide 24: That's it! — PPTX slide 29; content: centered big text + arc42 summary; WIP ribbon
- [~] Slide 25: That's it? — PPTX slide 31; content: centered transition to LASR; WIP ribbon
- [~] Slide 26: What is LASR — PPTX slide 32; content: 6-property card layout (lightweight/agile/gamified…); WIP ribbon
- [~] Slide 27: LASR Setup — PPTX slide 33; content: 5 prerequisites with icons; WIP ribbon
- [~] Slide 28: LASR Setup (repeat) — PPTX slide 34; content: same as 27; WIP ribbon
- [~] Slide 29: LASR Overview — PPTX slide 35; content: two-column Core Review vs LASR+ layout; WIP ribbon
- [~] Slide 30: Understand what makes you special — PPTX slide 36; content: 3 key questions with teal accent; WIP ribbon
- [~] Slide 31: Lean mission statement — PPTX slide 37; content: Netflix/DeepL/Prometheus/Threema examples; WIP ribbon
- [~] Slide 32: Lean mission statement (repeat) — PPTX slide 38; content: same as 31; WIP ribbon
- [~] Slide 33: Where to document? — PPTX slide 39; content: arc42 grid, ch.1 highlighted; WIP ribbon
- [~] Slide 34: Evaluation criteria — PPTX slide 40; content: find 3-5 quality attributes + weighting; WIP ribbon
- [~] Slide 35: Where to document? — PPTX slide 41; content: arc42 grid, ch.1+2 highlighted; WIP ribbon
- [~] Slide 36: Explore the architecture — PPTX slide 42; content: 3 exploration aspects (known/tradeoffs/problems); WIP ribbon
- [~] Slide 37: Risk-based review — PPTX slide 43; content: points-as-percentage + priority guidance; WIP ribbon
- [~] Slide 38: Where to document? — PPTX slide 44; content: arc42 grid, ch.9 highlighted; WIP ribbon
- [~] Slide 39: Quality-focused analysis (step 1) — PPTX slide 45; content: progressive step reveal, step 1 active; WIP ribbon
- [~] Slide 40: Quality-focused analysis (step 2) — PPTX slide 46; content: step 2 active; WIP ribbon
- [~] Slide 41: Quality-focused analysis (pro-tip) — PPTX slide 47; content: step 3 active (Utility-Tree); WIP ribbon
- [~] Slide 42: Quality-focused analysis (pro-tip repeat) — PPTX slide 48; content: step 3 active; WIP ribbon
- [~] Slide 43: Quality-focused analysis — PPTX slide 49; content: step 3 active (no source); WIP ribbon
- [~] Slide 44: Quality prioritization matrix — PPTX slide 50; content: 2x2 Business×Risk matrix; WIP ribbon
- [~] Slide 45: Bottom-Up vs Top-Down — PPTX slide 51; content: two-column analysis approaches; WIP ribbon
- [~] Slide 46: Bottom-Up vs Top-Down (repeat) — PPTX slide 52; content: same as 45; WIP ribbon
- [~] Slide 47: Bottom-Up vs Top-Down (repeat) — PPTX slide 53; content: same as 45; WIP ribbon
- [~] Slide 48: What now? — PPTX slide 54; content: 3 actions (derive/communicate/improve) with sub-bullets; WIP ribbon
- [~] Slide 49: Where to document? — PPTX slide 55; content: arc42 grid, ch.11+12 highlighted; WIP ribbon
- [~] Slide 50: That's it! (closing) — PPTX slide 56; content: large centered text; WIP ribbon
- [~] Slide 51: Start doing and keep on learning — PPTX slide 57; content: 4 resource links; WIP ribbon
- [~] Slide 52: Contact & Feedback — PPTX slide 58; content: LinkedIn contact + note; WIP ribbon
- [~] Slide 53: That's it, folks! — PPTX slide 59; content: large centered closing text (company email omitted per policy); WIP ribbon
