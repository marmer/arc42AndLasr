# arc42 & LASR Talk — Slide Progress

## Status legend
- `[ ]` pending
- `[~]` in progress
- `[x]` done

## 2026-06-10 — Full rebuild from the original deck

The first (hand-written HTML) conversion attempt was removed and replaced by a
generated, pixel-faithful conversion:

- Source of truth is the rendered PDF of the original talk
  (`arc42AndLasr_talk - envite_original_rendered.pdf`, 53 pages = the 53
  visible slides of the PPTX; PPTX slides 2, 3, 4, 6, 18, 30 are hidden and
  therefore excluded).
- `scripts/build_presentation.py` strips all company branding from the PDF
  (logo on every page, tagline on first/last page, company e-mail, vCard QR
  code regenerated without company data), exports every page as a vector SVG
  (`docs/img/slide-NN.svg`, text as paths → no font dependencies), extracts
  titles and speaker notes from the PPTX and generates `docs/index.html`.
- Every slide is one full-bleed SVG in its own `<section>`; speaker notes from
  the original PPTX are embedded as `<aside class="notes">`.
- Contact data on the final slide: e-mail replaced with
  `mariano.mertinat@gmail.com`, QR code regenerated as a clean vCard pointing
  to https://arc42andlasr.marmer.online.
- Verified in Chromium: slides 1, 10, 29 and 53 match the original PDF pages;
  no `envite`/`novatec`/conference references remain in `docs/`.

## Slides

- [x] Slide 01: arc42 and LASR
- [x] Slide 02: Who is this talk for?
- [x] Slide 03: ME
- [x] Slide 04: Warm Up - What can possibly happen?
- [x] Slide 05: Warm Up - What can possibly happen?
- [x] Slide 06: Warm Up - What can possibly happen?
- [x] Slide 07: Warm Up - What can possibly happen?
- [x] Slide 08: Warm Up - What can possibly happen?
- [x] Slide 09: Warm Up - What can possibly happen?
- [x] Slide 10: Warm Up - Now what?
- [x] Slide 11: Warm Up – use proven methods
- [x] Slide 12: ARC42 & LASR
- [x] Slide 13: Template for documentation
- [x] Slide 14: arc42 Template
- [x] Slide 15: arc42 Template
- [x] Slide 16: arc42 Template
- [x] Slide 17: arc42 Template
- [x] Slide 18: arc42 Template
- [x] Slide 19: arc42 Template
- [x] Slide 20: arc42 Template
- [x] Slide 21: arc42 Template
- [x] Slide 22: arc42 Template
- [x] Slide 23: arc42 Template
- [x] Slide 24: THAT‘s it!
- [x] Slide 25: THAT‘s it?
- [x] Slide 26: What is LASR (Lightweight Approach for Software Reviews)
- [x] Slide 27: As many stakeholders as possible
- [x] Slide 28: As many stakeholders as possible – at least you
- [x] Slide 29: LASR - Overview
- [x] Slide 30: Why is your system better than others
- [x] Slide 31: System slogans and lean mission statement
- [x] Slide 32: System slogans and lean mission statement
- [x] Slide 33: Where to document?
- [x] Slide 34: Find the 3-5 most important quality attributes
- [x] Slide 35: Where to document?
- [x] Slide 36: Explore the architecture
- [x] Slide 37: Risk-based review
- [x] Slide 38: Where to document?
- [x] Slide 39: Quality-focused analysis
- [x] Slide 40: Quality-focused analysis
- [x] Slide 41: Quality-focused analysis
- [x] Slide 42: Quality-focused analysis
- [x] Slide 43: Quality-focused analysis
- [x] Slide 44: Quality-focused analysis
- [x] Slide 45: Quality-focused analysis
- [x] Slide 46: Quality-focused analysis
- [x] Slide 47: Quality-focused analysis
- [x] Slide 48: You got some results – What now?
- [x] Slide 49: Where to document?
- [x] Slide 50: THAT‘s it!
- [x] Slide 51: Start doing and keep on learning!
- [x] Slide 52: ME (Feedback)
- [x] Slide 53: That‘s it folks
