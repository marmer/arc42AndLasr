#!/usr/bin/env python3
"""
Static quality checks for a completed slide.

Usage:
    python scripts/quality_check.py --slide <N>

Checks:
    1. No banned company / conference references
    2. Speaker notes <aside> present and non-empty
    3. No large inline SVGs (should be externalized to docs/img/)
    4. docs/progress.md has an entry for this slide

Exit codes:
    0  All checks passed
    1  One or more checks failed
    2  Error (file not found, etc.)

Output: JSON  {"slide": N, "status": "PASS"|"FAIL", "failures": [...]}
"""
import sys
import json
import re
import argparse
from pathlib import Path

BANNED_REFS = [
    'novatec',
    'envite',
    'it-tage',
    'it tage',
    'software quality days',
    'decompiled',
    'softwarearchitektur-konferenz',
]

# Inline SVGs longer than this many lines are considered "should be externalized"
INLINE_SVG_LINE_THRESHOLD = 25


def check_slide(slide_num: int) -> list[str]:
    failures = []

    slide_file = Path(f"docs/slides/slide-{slide_num:02d}.html")
    if not slide_file.exists():
        return [f"Slide file not found: {slide_file}"]

    content = slide_file.read_text(encoding='utf-8')
    content_lower = content.lower()

    # ── Check 1: Banned references ────────────────────────────────────────────
    for ref in BANNED_REFS:
        if ref in content_lower:
            failures.append(f"Banned reference found: '{ref}'")

    # ── Check 2: Speaker notes present and non-empty ──────────────────────────
    # Accept both attribute orderings: class="notes" and aria-label="speaker notes"
    has_notes_tag = bool(
        re.search(r'<aside\b[^>]*\bclass=["\']notes["\']', content)
        or re.search(r'<aside\b[^>]*aria-label=["\']speaker notes["\']', content)
    )
    if not has_notes_tag:
        failures.append("Speaker <aside class=\"notes\"> element missing")
    else:
        # Check content is not just whitespace
        notes_match = re.search(
            r'<aside\b[^>]*(?:class=["\']notes["\']|aria-label=["\']speaker notes["\'])[^>]*>'
            r'(.*?)</aside>',
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if notes_match and not notes_match.group(1).strip():
            failures.append("Speaker notes <aside> exists but is empty")

    # ── Check 3: No large inline SVGs ─────────────────────────────────────────
    inline_svgs = re.findall(r'<svg\b[^>]*>.*?</svg>', content, re.DOTALL)
    for svg in inline_svgs:
        line_count = svg.count('\n')
        if line_count > INLINE_SVG_LINE_THRESHOLD:
            failures.append(
                f"Large inline SVG ({line_count} lines) — extract to docs/img/ and reference via <img>"
            )

    # ── Check 4: progress.md has an entry for this slide ─────────────────────
    progress_file = Path("docs/progress.md")
    if progress_file.exists():
        progress = progress_file.read_text(encoding='utf-8')
        if not re.search(rf'Slide\s+{slide_num}\s*:', progress, re.IGNORECASE):
            failures.append(f"docs/progress.md has no entry for Slide {slide_num}")
    else:
        failures.append("docs/progress.md not found")

    return failures


def main():
    parser = argparse.ArgumentParser(description='Quality check for a completed slide')
    parser.add_argument('--slide', type=int, required=True, help='Slide number (e.g. 14)')
    args = parser.parse_args()

    try:
        failures = check_slide(args.slide)
    except Exception as exc:
        print(json.dumps({"slide": args.slide, "status": "ERROR", "failures": [str(exc)]}))
        sys.exit(2)

    result = {
        "slide": args.slide,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    sys.exit(0 if not failures else 1)


if __name__ == '__main__':
    main()
