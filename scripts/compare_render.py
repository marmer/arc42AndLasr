#!/usr/bin/env python3
"""Screenshot every Reveal.js slide and compare it with the reference PDF render.

Writes per-slide composites (reference | reveal | diff) into screenshots/compare/
and prints a diff score per slide (RMS of pixel difference, 0 = identical).

Usage:
    python3 scripts/compare_render.py [--slides 1,2,5] [--port 8123]

Requires work/ref_pdf/pNN.png (created from the original rendered PDF) and a
generated docs/index.html.
"""
import argparse
import functools
import http.server
import io
import math
import os
import sys
import threading

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
W, H = 960, 540


def serve(port):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=os.path.join(ROOT, 'docs'))
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slides', default=None, help='comma separated 1-based slide numbers')
    ap.add_argument('--port', type=int, default=8123)
    ap.add_argument('--state', choices=['final', 'initial'], default='final',
                    help='fragment state to capture')
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, 'screenshots', 'compare')
    os.makedirs(out_dir, exist_ok=True)
    serve(args.port)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        page.goto(f'http://127.0.0.1:{args.port}/index.html')
        page.wait_for_function('window.Reveal && Reveal.isReady()')
        page.wait_for_timeout(1500)  # fonts
        total = page.evaluate('Reveal.getTotalSlides()')
        wanted = (sorted(int(s) for s in args.slides.split(',')) if args.slides
                  else list(range(1, total + 1)))
        scores = []
        for n in wanted:
            frag = 99 if args.state == 'final' else -1
            page.evaluate(f'Reveal.slide({n - 1}, 0, {frag})')
            page.wait_for_function('Array.from(document.images).every(i => i.complete)',
                                   timeout=15000)
            page.wait_for_timeout(250)
            shot = page.screenshot()
            img = Image.open(io.BytesIO(shot)).convert('RGB')
            ref_path = os.path.join(ROOT, 'work', 'ref_pdf', f'p{n:02d}.png')
            if os.path.exists(ref_path):
                ref = Image.open(ref_path).convert('RGB').resize((W, H))
                diff = ImageChops.difference(ref, img)
                hist = diff.convert('L').histogram()
                sq = sum(v * (i ** 2) for i, v in enumerate(hist))
                rms = math.sqrt(sq / (W * H))
                scores.append((rms, n))
                comp = Image.new('RGB', (W, H * 3 + 20), 'white')
                comp.paste(ref, (0, 0))
                comp.paste(img, (0, H + 10))
                comp.paste(diff, (0, 2 * H + 20))
                comp.save(os.path.join(out_dir, f'slide{n:02d}.png'))
                print(f'slide {n:2d}: rms={rms:7.2f}')
            else:
                img.save(os.path.join(out_dir, f'slide{n:02d}.png'))
                print(f'slide {n:2d}: no reference')
        browser.close()
    if scores:
        scores.sort(reverse=True)
        print('\nworst slides:', ', '.join(f'{n}({rms:.0f})' for rms, n in scores[:12]))


if __name__ == '__main__':
    main()
