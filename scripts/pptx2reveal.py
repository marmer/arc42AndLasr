#!/usr/bin/env python3
"""Convert the original arc42+LASR PPTX into a Reveal.js presentation.

Translates DrawingML shape coordinates (EMU) directly into absolutely
positioned HTML on a 960x540 canvas so that identical shapes land on
identical pixels across slides (no visual jumps). PowerPoint entrance
animations (p:timing) become Reveal.js fragments.

Usage:
    python3 scripts/pptx2reveal.py "<pptx>" docs
"""
import hashlib
import html as html_mod
import io
import math
import os
import re
import sys
import zipfile

import fitz  # PyMuPDF
import qrcode
from lxml import etree
from PIL import Image

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
}
EMU_PER_PX = 9525.0          # 96 dpi
PT_TO_PX = 96.0 / 72.0
LINE_BASE = 1.2              # CSS line-height for 100% PowerPoint spacing

BANNED_RE = re.compile(r'(?i)envite|novatec|it-?tage|decompile|software\s*quality\s*days'
                       r'|pioneering\s+it\s+sustainability')
# (pattern, replacement) applied to run text before the banned check
TEXT_REPLACEMENTS = [
    (re.compile(r'(?i)mariano\.mertinat@envite\.de'), 'mariano.mertinat@gmail.com'),
    (re.compile(r'\+49[\s\d]{8,18}'), ''),
    # author bio updated after the PPTX was written (commits "Revise slide
    # content and layout in slide1.html" / "Change author description in
    # slide1.html"); anchored to the exact run texts of the title slide
    (re.compile(r'^Software-$'), 'Software- and Solution-'),
    (re.compile(r'^, Consultant, Nerd$'), ', Trainer, Father, Nerd'),
]
# media parts that must never be emitted (company logos)
BANNED_MEDIA = {'ppt/media/image2.png'}
# media parts replaced with generated content (e.g. the contact vCard QR code)
VCARD = ('BEGIN:VCARD\nVERSION:2.1\nN;CHARSET=UTF-8:Mertinat;Mariano\n'
         'FN;CHARSET=UTF-8:Mariano Mertinat\n'
         'TITLE;CHARSET=UTF-8:software-architect / solution-architect / trainer\n'
         'EMAIL:mariano.mertinat@gmail.com\nURL:https://marmer.online\nEND:VCARD')


def _make_qr_png():
    img = qrcode.make(VCARD, box_size=10, border=0)
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return buf.getvalue()


# the title slide's background photo is employer-branded; replaced (see
# render_pic) with the inline animated SVG below instead of a raster image
TITLE_BG_MEDIA = 'ppt/media/image3.jpeg'


def _title_bg_svg(W=960, H=540):
    """Inline animated SVG for the title-slide background.

    License-free, procedurally drawn golden-hour ridgeline that keeps the
    original photo's impression (warm wide-open nature, distant haze) plus two
    stick figures tossing a ball back and forth — a nod to the "playful"
    subtitle. Inline so the SMIL ball animation actually runs (it would not in
    an <img>-referenced SVG). Fully generated -> no licensing risk.
    """
    import math

    def ridge_d(base_t, amp_t, f1, f2, ph):
        base, amp = H * base_t, H * amp_t
        pts = [(x, base - amp * (math.sin(x / W * math.pi * f1 + ph) * 0.6
                                 + math.sin(x / W * math.pi * f2 + ph * 1.7) * 0.4))
               for x in range(0, W + 1, 8)]
        d = 'M %.1f %.1f ' % pts[0] + ' '.join('L %.1f %.1f' % p for p in pts[1:])
        return d + ' L %d %d L 0 %d Z' % (W, H, H), pts

    d_far, _ = ridge_d(0.585, 0.05, 3, 7, 0.4)
    d_mid1, _ = ridge_d(0.66, 0.07, 2.2, 5, 1.1)
    d_mid2, _ = ridge_d(0.74, 0.08, 1.7, 4.3, 2.2)

    fg_base, fg_amp = H * 0.80, H * 0.13
    fpts = [(x, fg_base - fg_amp * (math.sin(x / W * math.pi * 1.3 + 0.6) * 0.6
                                    + math.sin(x / W * math.pi * 3.1 + 1.0) * 0.4))
            for x in range(0, W + 1, 8)]
    d_fg = ('M %.1f %.1f ' % fpts[0] + ' '.join('L %.1f %.1f' % p for p in fpts[1:])
            + ' L %d %d L 0 %d Z' % (W, H, H))

    # the throwing arm's hand swings between a raised pose (throw/catch) and a
    # lowered pose (resting), in sync with the ball. The left figure is raised
    # when the ball is at its hand (cycle ends t=0/1); the right at t=0.5.
    EASE = 'calcMode="spline" keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"'

    def figure(cx, s, facing, raised_first):
        yb = min(fpts, key=lambda p: abs(p[0] - cx))[1]
        shoulder = (cx, yb - 13 * s)
        raised = (cx + 5 * s * facing, yb - 19 * s)   # hand up toward partner
        lowered = (cx + 4 * s * facing, yb - 9 * s)   # hand relaxed/down
        static = [(cx, yb - 14 * s, cx, yb - 5 * s),                # torso
                  (cx, yb - 5 * s, cx - 2 * s, yb + 1 * s),         # legs
                  (cx, yb - 5 * s, cx + 2 * s, yb + 1 * s),
                  (cx, yb - 13 * s, cx - 3 * s * facing, yb - 8 * s)]  # trailing arm
        lines = ''.join('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % seg for seg in static)
        a, b = (raised, lowered) if raised_first else (lowered, raised)
        arm = ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f">'
               '<animate attributeName="x2" dur="2.4s" repeatCount="indefinite" %s values="%.1f;%.1f;%.1f"/>'
               '<animate attributeName="y2" dur="2.4s" repeatCount="indefinite" %s values="%.1f;%.1f;%.1f"/>'
               '</line>') % (shoulder[0], shoulder[1], a[0], a[1],
                             EASE, a[0], b[0], a[0], EASE, a[1], b[1], a[1])
        g = ('<g stroke="#28221a" stroke-width="%.2f" stroke-linecap="round" fill="#28221a">'
             '<circle cx="%.1f" cy="%.1f" r="%.1f"/>%s%s</g>'
             % (2 * s, cx, yb - 16 * s, 2 * s, lines, arm))
        return g, raised

    sL, sR = 1.7, 1.6
    gL, hL = figure(W * 0.80, sL, +1, raised_first=True)    # raised at t=0/1
    gR, hR = figure(W * 0.852, sR, -1, raised_first=False)  # raised at t=0.5
    midx = (hL[0] + hR[0]) / 2
    peak = min(hL[1], hR[1]) - 15 * (sL + sR) / 2
    # there-and-back arc so the ball is tossed L->R then R->L, repeating
    ball_path = ('M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f'
                 % (hL[0], hL[1], midx, peak, hR[0], hR[1], midx, peak, hL[0], hL[1]))
    br = 2.2 * (sL + sR) / 2

    return f'''<svg viewBox="0 0 {W} {H}" width="100%" height="100%" preserveAspectRatio="none" \
xmlns="http://www.w3.org/2000/svg" style="display:block">
<defs>
<linearGradient id="tbSky" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H * 0.6:.0f}">
<stop offset="0" stop-color="rgb(150,178,196)"/><stop offset="0.6" stop-color="rgb(210,214,202)"/>
<stop offset="1" stop-color="rgb(248,226,176)"/></linearGradient>
<radialGradient id="tbSun" gradientUnits="userSpaceOnUse" cx="{W * 0.73:.0f}" cy="{H * 0.5:.0f}" r="{W * 0.46:.0f}">
<stop offset="0" stop-color="rgb(255,247,222)" stop-opacity="0.85"/>
<stop offset="1" stop-color="rgb(255,247,222)" stop-opacity="0"/></radialGradient>
<linearGradient id="tbFg" gradientUnits="userSpaceOnUse" x1="0" y1="{H * 0.66:.0f}" x2="0" y2="{H}">
<stop offset="0" stop-color="rgb(214,180,104)"/><stop offset="1" stop-color="rgb(92,74,42)"/></linearGradient>
<filter id="tbBlur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDev="13"/></filter>
<radialGradient id="tbVig" gradientUnits="userSpaceOnUse" cx="{W / 2:.0f}" cy="{H / 2:.0f}" r="{W * 0.62:.0f}">
<stop offset="0.62" stop-color="#000" stop-opacity="0"/>
<stop offset="1" stop-color="rgb(20,18,14)" stop-opacity="0.4"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#tbSky)"/>
<rect width="{W}" height="{H}" fill="url(#tbSun)"/>
<ellipse cx="{W * 0.5:.0f}" cy="{H * 0.6:.0f}" rx="{W * 0.6:.0f}" ry="24" fill="rgb(244,243,238)" \
opacity="0.7" filter="url(#tbBlur)"/>
<path d="{d_far}" fill="rgb(150,168,180)" opacity="0.92"/>
<path d="{d_mid1}" fill="rgb(120,140,110)"/>
<path d="{d_mid2}" fill="rgb(96,112,72)"/>
<path d="{d_fg}" fill="url(#tbFg)"/>
{gL}{gR}
<circle cx="0" cy="0" r="{br:.1f}" fill="rgb(252,247,235)" stroke="#28221a" stroke-width="0.7">
<animateMotion dur="2.4s" repeatCount="indefinite" path="{ball_path}" calcMode="spline" \
keyTimes="0;0.5;1" keyPoints="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>
</circle>
<rect width="{W}" height="{H}" fill="url(#tbVig)"/>
</svg>'''


REPLACED_MEDIA = {
    'ppt/media/image80.png': _make_qr_png,
}
A14_NS = 'http://schemas.microsoft.com/office/drawing/2010/main'

# Descriptive output file names. Keyed by (source basename, variant) for
# embedded media; keyed by "<pdfPage>x<xref>" for bitmaps lifted out of the
# rendered PDF. Identical content is de-duplicated to a single file, so an
# icon reused on several slides keeps one speaking name; genuinely distinct
# images that would share a slug get a numeric suffix.
MEDIA_SLUGS = {
    ('image1.jpeg', ''): 'closing-background',
    ('image79.jpg', ''): 'speaker-portrait',
    ('image21.png', ''): 'gear-warning-icon',
    ('image22.png', ''): 'yawning-person-icon',
    ('image27.png', ''): 'hello-badge',
    ('image28.jfif', ''): 'linkedin-qr',
    ('image29.png', ''): 'article-cobol-wanted',
    ('image30.png', ''): 'article-healthcare-gov',
    ('image31.png', ''): 'news-prisoners-released',
    ('image32.png', ''): 'article-ambulance-glitch',
    ('image33.png', ''): 'comic-humans-vs-computers',
    ('image34.png', ''): 'questions-doodle',
    ('image35.png', ''): 'tech-network-emblem',
    ('image39.png', 'duo296354FFFFFF'): 'chess-knight-icon',
    ('image40.png', ''): 'building-block-zoom',
    ('image41.png', 'duo296354FFFFFF'): 'arrows-outward-icon',
    ('image46.png', ''): 'thats-it-folks-rings',
    ('image48.png', ''): 'isaqb-logo',
    ('image51.jpg', ''): 'arc42-by-example-book',
    ('image52.png', ''): 'arc42-in-aktion-book',
    ('image58.png', ''): 'lasr-overview',
    ('image58.png', 'duo6D6D6DFFFFFF'): 'lasr-overview-grey',
    ('image59.png', ''): 'lasr-deepdive-steps',
    ('image60.png', ''): 'netflix-signup',
    ('image61.png', ''): 'deepl-translation',
    ('image62.png', ''): 'metrics-to-insight',
    ('image63.png', ''): 'vpn-secure-anonymous',
    ('image66.png', ''): 'encryption-privacy-text',
    ('image67.png', ''): 'lasr-plus-radar',
    ('image68.png', ''): 'sharpen-results-checklist',
    ('image69.png', ''): 'utility-tree-example',
    ('image70.png', ''): 'utility-tree-detailed',
    ('image70.png', 'duo6D6D6DFFFFFF'): 'utility-tree-detailed-grey',
    ('image72.png', ''): 'quality-criteria-form',
    ('image73.png', ''): 'performance-efficiency-card',
    ('image74.png', ''): 'reviewing-software-systems-book-de',
    ('image75.png', ''): 'analyze-improve-cycle',
    ('image76.png', ''): 'reviewing-software-systems-book-en',
    ('image77.png', ''): 'hello-badge',
    ('image78.png', ''): 'teal-square',
    ('image80.png', ''): 'contact-vcard-qr',
    # yellow marker ink strokes (mc:Fallback bitmaps) on the Threema quote
    ('image450.png', ''): 'marker-no-personal-data',
    ('image460.png', ''): 'marker-used',
    ('image470.png', ''): 'marker-anonymously',
    ('image480.png', ''): 'marker-without',
    ('image490.png', ''): 'marker-phone-or-email',
    ('image500.png', ''): 'marker-privacy-by-design',
    ('image510.png', ''): 'marker-swiss-made',
    ('image520.png', ''): 'marker-gdpr-compliant',
    ('image530.png', ''): 'marker-end-to-end-encryption',
}

# Ink strokes that drew the smiley face onto the original alien badge
# artwork (slides 7/58) — that artwork is redrawn as hello-badge.svg /
# feedback-badge.svg without the alien, so the face doodle goes with it.
SKIPPED_INK_MEDIA = {'ppt/media/image180.png', 'ppt/media/image190.png',
                     'ppt/media/image200.png', 'ppt/media/image210.png'}
PDF_SLUGS = {
    '14x164': 'target-dartboard-icon',
    '15x180': 'gears-lock-icon',
    '16x196': 'circuit-network-icon',
    '20x272': 'checklist-gear-icon',
    '21x288': 'circuit-checks-icon',
    '22x304': 'paper-whirl-icon',
    '23x320': 'book-magnifier-icon',
    '25x340': 'thats-it-folks-rings-grey',
    '26x362': 'feather-icon',
    '26x364': 'person-suit-icon',
    '26x366': 'gamepad-icon',
    '26x368': 'running-person-icon',
    '27x372': 'audience-people-icon',
    '28x372': 'audience-people-icon',
    '31x398': 'privacy-bubbles-blue',
    '31x400': 'privacy-bubbles-green',
    '32x398': 'privacy-bubbles-blue',
    '32x400': 'privacy-bubbles-green',
    '34x429': 'gamepad-icon',
    '36x470': 'warning-electric-icon',
    '36x472': 'document-magnifier-icon',
    '37x477': 'gamepad-icon',
    '42x528': 'lasr-scenario-cards',
    '45x366': 'gamepad-icon',
    '45x472': 'document-magnifier-icon',
    '46x366': 'gamepad-icon',
    '47x366': 'gamepad-icon',
    '50x723': 'thats-it-folks-rings-color',
    '51x340': 'thats-it-folks-rings-grey-faded',
}

# Hand-drawn animated SVG replacements (assets/svg/) for the supporting
# images, keyed by the *final* docs/img file name (after slug + dedup
# suffixing). Value: (svg file, optional fit box). The SVG is inlined into
# the slide HTML (so webfonts + CSS animations apply) inside a wrapper
# marked data-svg-replaced, which compare_render.py uses to mask the region.
# The fit box (fractions x0,y0,x1,y1 of the replaced bitmap's canvas) scales
# the artwork into padded canvases (the PDF-extracted ring bitmaps carry
# large transparent margins).
# Slides the author cut from the web deck even though they are visible in
# the PPTX (slide59: duplicate closing/contact slide, removed in commit
# "Last slide removed").
DROPPED_SLIDES = {'slide59.xml'}

SVG_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '..', 'assets', 'svg')
SVG_REPLACEMENTS = {
    # slide 2: fit boxes shrink the artwork to the original bitmap content
    # size (the raster originals carry transparent margins the SVGs lack)
    'gear-warning-icon.png': ('gear-warning.svg',
                              (0.064, 0.038, 0.930, 0.904)),
    'yawning-person-icon.png': ('yawning-person.svg',
                                (0.071, -0.076, 0.996, 0.849)),
    'hello-badge.png': ('hello-badge.svg', None),
    'hello-badge-2.png': ('feedback-badge.svg', None),
    'questions-doodle.png': ('questions-doodle.svg', None),
    'tech-network-emblem.png': ('tech-network-emblem.svg', None),
    'target-dartboard-icon.png': ('target-dartboard.svg', None),
    'gears-lock-icon.png': ('gears-lock.svg', None),
    'circuit-network-icon.png': ('circuit-network.svg', None),
    'chess-knight-icon.png': ('chess-knight.svg', None),
    'arrows-outward-icon.png': ('arrows-outward.svg', None),
    'checklist-gear-icon.png': ('checklist-gear.svg', None),
    'circuit-checks-icon.png': ('circuit-checks.svg', None),
    'paper-whirl-icon.png': ('paper-whirl.svg', None),
    'book-magnifier-icon.png': ('book-magnifier.svg', None),
    'thats-it-folks-rings.png': ('thats-it-folks-rings.svg', None),
    'thats-it-folks-rings-color.png': ('thats-it-folks-rings.svg',
                                       (0.13, 0.17, 0.88, 0.84)),
    'thats-it-folks-rings-grey.png': ('thats-it-folks-rings-grey.svg',
                                      (0.13, 0.17, 0.88, 0.84)),
    'feather-icon.png': ('feather.svg', None),
    'person-suit-icon.png': ('person-suit.svg', None),
    'running-person-icon.png': ('running-person.svg', None),
    # the PDF-extracted gamepad/warning/document bitmaps carry large
    # transparent margins, so a full-canvas SVG rendered oversized (the two
    # icons overlapped on slide 45). Each fit box is a square sub-viewport
    # that puts the SVG artwork (which has its own margins inside the
    # viewBox) at the position and size of the original bitmap content.
    'gamepad-icon.png': ('gamepad.svg', (0.177, 0.169, 0.817, 0.809)),
    'gamepad-icon-2.png': ('gamepad.svg', (0.177, 0.169, 0.817, 0.809)),
    'gamepad-icon-3.png': ('gamepad.svg', (0.177, 0.169, 0.817, 0.809)),
    'audience-people-icon.png': ('audience-people.svg', None),
    'warning-electric-icon.png': ('warning-electric.svg',
                                  (0.087, 0.058, 0.962, 0.933)),
    'document-magnifier-icon.png': ('document-magnifier.svg',
                                    (0.024, -0.005, 0.993, 0.964)),
    'analyze-improve-cycle.png': ('analyze-improve-cycle.svg', None),
}

# Deliberate position deviations from the PPTX, keyed by
# (slide xml basename, final docs/img file name) -> (left, top) in px.
# The gamepad "workshop game" marker pokes half into the title bar on
# slides 46/47 — pin it to the position it has on slides 34/37. Slide 45's
# gamepad stays at its PPTX position next to the "Top Down" bullet (an
# earlier override there was reverted on the author's request).
PIC_POS_OVERRIDES = {
    ('slide52.xml', 'gamepad-icon.png'): (698.7, 110.7),
    ('slide53.xml', 'gamepad-icon.png'): (698.7, 110.7),
}

# Deliberate z-order deviations from the PPTX, keyed by
# (slide xml basename, shape name) -> CSS z-index. The closing slide's
# title hides behind the "THAT'S IT FOLKS" rings in the original deck —
# lift it above the artwork (author's request).
SHAPE_Z_OVERRIDES = {
    ('slide57.xml', 'Textplatzhalter 4'): 1,
}

BULLET_CHAR_MAP = {
    ('Wingdings', '§'): '▪',
    ('Wingdings', 'Ø'): '➢',
    ('Wingdings', 'ü'): '✓',
    ('Wingdings', 'v'): '❖',
    ('Symbol', '-'): '−',
    ('Symbol', '·'): '•',
}


def q(tag):
    pfx, local = tag.split(':')
    return f'{{{NS[pfx]}}}{local}'


class Pkg:
    def __init__(self, path):
        self.zf = zipfile.ZipFile(path)
        self.names = set(self.zf.namelist())
        self._cache = {}

    def read(self, name):
        return self.zf.read(name)

    def xml(self, name):
        if name not in self._cache:
            self._cache[name] = etree.fromstring(self.zf.read(name))
        return self._cache[name]

    def rels(self, part):
        d, b = os.path.split(part)
        rp = f'{d}/_rels/{b}.rels'
        out = {}
        if rp in self.names:
            for rel in self.xml(rp):
                target = rel.get('Target')
                mode = rel.get('TargetMode', 'Internal')
                if mode == 'Internal':
                    target = os.path.normpath(os.path.join(d, target)).replace('\\', '/')
                out[rel.get('Id')] = (target, mode)
        return out


def emu2px(v):
    return float(v) / EMU_PER_PX


def esc(s):
    return html_mod.escape(s, quote=False)


def fmt(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


# ---------------------------------------------------------------- color


def _clamp(x):
    return max(0.0, min(1.0, x))


def _rgb_to_hsl(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6, s, l


def _hsl_to_rgb(h, s, l):
    if s == 0:
        return l, l, l

    def f(p, qq, t):
        t %= 1
        if t < 1 / 6:
            return p + (qq - p) * 6 * t
        if t < 1 / 2:
            return qq
        if t < 2 / 3:
            return p + (qq - p) * (2 / 3 - t) * 6
        return p

    qq = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - qq
    return f(p, qq, h + 1 / 3), f(p, qq, h), f(p, qq, h - 1 / 3)


class Ctx:
    """Per-slide resolution context: theme colors, clrMap, fonts."""

    def __init__(self, theme_colors, clr_map, fonts):
        self.theme_colors = theme_colors
        self.clr_map = clr_map
        self.fonts = fonts  # {'major': 'DM Sans', 'minor': 'Karla'}


def resolve_color(el, ctx):
    """el = a color element (a:srgbClr / a:schemeClr / ...). -> (hex, alpha)"""
    tag = etree.QName(el).localname
    if tag == 'srgbClr':
        hexv = el.get('val')
    elif tag == 'sysClr':
        hexv = el.get('lastClr', '000000')
    elif tag == 'schemeClr':
        name = el.get('val')
        name = ctx.clr_map.get(name, name)
        hexv = ctx.theme_colors.get(name, '000000')
    elif tag == 'prstClr':
        hexv = {'black': '000000', 'white': 'FFFFFF'}.get(el.get('val'), '808080')
    else:
        hexv = '000000'
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (0, 2, 4))
    alpha = 1.0
    for ch in el:
        t = etree.QName(ch).localname
        v = ch.get('val')
        if v is None:
            continue
        f = int(v) / 100000
        if t == 'alpha':
            alpha = f
        elif t == 'tint':
            r, g, b = (c * f + (1 - f) for c in (r, g, b))
        elif t == 'shade':
            r, g, b = (c * f for c in (r, g, b))
        elif t == 'lumMod':
            h, s, l = _rgb_to_hsl(r, g, b)
            r, g, b = _hsl_to_rgb(h, s, _clamp(l * f))
        elif t == 'lumOff':
            h, s, l = _rgb_to_hsl(r, g, b)
            r, g, b = _hsl_to_rgb(h, s, _clamp(l + f))
        elif t == 'satMod':
            h, s, l = _rgb_to_hsl(r, g, b)
            r, g, b = _hsl_to_rgb(h, _clamp(s * f), l)
    hexv = '%02X%02X%02X' % tuple(int(round(_clamp(c) * 255)) for c in (r, g, b))
    return hexv, alpha


def css_color(hexv, alpha):
    if alpha >= 0.999:
        return f'#{hexv}'
    r, g, b = int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16)
    return f'rgba({r},{g},{b},{alpha:.3f})'


def fill_css(fill_el, ctx, w=None, h=None):
    """fill_el: a:solidFill / a:gradFill / a:noFill / a:pattFill. -> CSS background or None.

    w/h (px) let scaled linear gradients stretch their angle to the shape's
    aspect ratio the way PowerPoint does (45deg = corner to corner)."""
    if fill_el is None:
        return None
    tag = etree.QName(fill_el).localname
    if tag == 'noFill':
        return 'transparent'
    if tag == 'solidFill':
        c = fill_el[0]
        return css_color(*resolve_color(c, ctx))
    if tag == 'gradFill':
        stops = []
        for gs in fill_el.findall(q('a:gsLst') + '/' + q('a:gs')):
            pos = int(gs.get('pos')) / 1000
            col = css_color(*resolve_color(gs[0], ctx))
            stops.append((pos, col))
        stops.sort(key=lambda s: s[0])
        lin = fill_el.find(q('a:lin'))
        ang = 90.0
        if lin is not None:
            ang = int(lin.get('ang', '0')) / 60000.0
            if lin.get('scaled') == '1' and w and h:
                rad = math.radians(ang)
                ang = math.degrees(math.atan2(h * math.sin(rad), w * math.cos(rad))) % 360
        css_ang = (ang + 90.0) % 360
        stop_s = ', '.join(f'{c} {p:.1f}%' for p, c in stops)
        return f'linear-gradient({css_ang:.1f}deg, {stop_s})'
    if tag == 'pattFill':
        fg = fill_el.find(q('a:fgClr'))
        bg = fill_el.find(q('a:bgClr'))
        fgc = css_color(*resolve_color(fg[0], ctx)) if fg is not None else '#000'
        bgc = css_color(*resolve_color(bg[0], ctx)) if bg is not None else '#fff'
        return (f'repeating-linear-gradient(45deg, {fgc} 0 2px, {bgc} 2px 6px)')
    return None


def find_fill(parent, ctx):
    """First direct fill child of parent (spPr etc.)."""
    if parent is None:
        return None
    for ch in parent:
        if etree.QName(ch).localname in ('solidFill', 'gradFill', 'noFill', 'pattFill', 'blipFill', 'grpFill'):
            return ch
    return None


# ---------------------------------------------------------------- styles


def style_sources(txbody, ph, layout_ph, master_ph, master, pres_default):
    """Ordered list of lstStyle-like elements for property lookup."""
    sources = []
    if txbody is not None:
        ls = txbody.find(q('a:lstStyle'))
        if ls is not None:
            sources.append(ls)
    for el in (layout_ph, master_ph):
        if el is not None:
            tb = el.find(q('p:txBody'))
            if tb is not None:
                ls = tb.find(q('a:lstStyle'))
                if ls is not None:
                    sources.append(ls)
    if master is not None:
        tx_styles = master.find(q('p:txStyles'))
        if tx_styles is not None:
            ph_type = ph.get('type', 'body') if ph is not None else None
            if ph_type in ('title', 'ctrTitle'):
                sources.append(tx_styles.find(q('p:titleStyle')))
            elif ph is not None:
                sources.append(tx_styles.find(q('p:bodyStyle')))
            else:
                sources.append(tx_styles.find(q('p:otherStyle')))
    if pres_default is not None:
        sources.append(pres_default)
    return [s for s in sources if s is not None]


def lvl_candidates(sources, lvl):
    out = []
    for src in sources:
        el = src.find(q(f'a:lvl{lvl + 1}pPr'))
        if el is None:
            el = src.find(q('a:defPPr'))
        if el is not None:
            out.append(el)
    return out


def para_attr(ppr, cands, name, default=None):
    if ppr is not None and ppr.get(name) is not None:
        return ppr.get(name)
    for c in cands:
        if c.get(name) is not None:
            return c.get(name)
    return default


def para_child(ppr, cands, tag):
    if ppr is not None:
        el = ppr.find(q(tag))
        if el is not None:
            return el
    for c in cands:
        el = c.find(q(tag))
        if el is not None:
            return el
    return None


def bullet_props(ppr, cands):
    """Resolve bullet: returns (kind, char_or_fmt, font, color_el, szpct). kind in none/char/autonum."""
    chain = ([ppr] if ppr is not None else []) + cands
    kind = None
    char = None
    fmtv = None
    bu_font = None
    bu_clr = None
    bu_sz = None
    for el in chain:
        if el is None:
            continue
        if kind is None:
            if el.find(q('a:buNone')) is not None:
                kind = 'none'
            elif el.find(q('a:buChar')) is not None:
                kind = 'char'
                char = el.find(q('a:buChar')).get('char')
            elif el.find(q('a:buAutoNum')) is not None:
                kind = 'autonum'
                fmtv = el.find(q('a:buAutoNum')).get('type', 'arabicPeriod')
        if bu_font is None and el.find(q('a:buFont')) is not None:
            bu_font = el.find(q('a:buFont')).get('typeface')
        if bu_clr is None and el.find(q('a:buClr')) is not None:
            bu_clr = el.find(q('a:buClr'))[0]
        if bu_sz is None and el.find(q('a:buSzPct')) is not None:
            bu_sz = int(el.find(q('a:buSzPct')).get('val')) / 100000
    return kind or 'none', char, fmtv, bu_font, bu_clr, bu_sz


def run_prop(rpr, cands, name, default=None):
    if rpr is not None and rpr.get(name) is not None:
        return rpr.get(name)
    for c in cands:
        d = c.find(q('a:defRPr'))
        if d is not None and d.get(name) is not None:
            return d.get(name)
    return default


def run_child(rpr, cands, tag):
    if rpr is not None:
        el = rpr.find(q(tag))
        if el is not None:
            return el
    for c in cands:
        d = c.find(q('a:defRPr'))
        if d is not None:
            el = d.find(q(tag))
            if el is not None:
                return el
    return None


def resolve_font(typeface, ctx):
    if typeface in (None, ''):
        return None
    if typeface in ('+mj-lt', '+mj-ea', '+mj-cs'):
        return ctx.fonts['major']
    if typeface in ('+mn-lt', '+mn-ea', '+mn-cs'):
        return ctx.fonts['minor']
    return typeface


AUTONUM_FMT = {
    'arabicPeriod': lambda n: f'{n}.',
    'arabicParenR': lambda n: f'{n})',
    'arabicPlain': lambda n: f'{n}',
    'alphaLcPeriod': lambda n: f'{chr(96 + n)}.',
    'alphaUcPeriod': lambda n: f'{chr(64 + n)}.',
    'romanLcPeriod': lambda n: f'{_roman(n).lower()}.',
    'romanUcPeriod': lambda n: f'{_roman(n)}.',
}


def _roman(n):
    vals = [(10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    out = ''
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


# ---------------------------------------------------------------- geometry helpers


def brace_path(w, h, left=True):
    """Approximate left/right curly brace as SVG path (stroke only)."""
    # pointing tip at mid height; drawn with cubic curves
    x0, x1 = (w, 0) if left else (0, w)
    xm = w / 2
    ym = h / 2
    r = min(w, h * 0.1)
    p = []
    p.append(f'M {x0:.1f} 0')
    p.append(f'C {xm:.1f} 0 {xm:.1f} {r:.1f} {xm:.1f} {r * 2:.1f}')
    p.append(f'L {xm:.1f} {ym - r * 2:.1f}')
    p.append(f'C {xm:.1f} {ym - r:.1f} {(xm + x1) / 2:.1f} {ym:.1f} {x1:.1f} {ym:.1f}')
    p.append(f'C {(xm + x1) / 2:.1f} {ym:.1f} {xm:.1f} {ym + r:.1f} {xm:.1f} {ym + r * 2:.1f}')
    p.append(f'L {xm:.1f} {h - r * 2:.1f}')
    p.append(f'C {xm:.1f} {h - r:.1f} {xm:.1f} {h:.1f} {x0:.1f} {h:.1f}')
    return ' '.join(p)


def custgeom_svg_path(geom, w, h):
    """Convert a:custGeom to an SVG path string scaled to w x h px."""
    paths = []
    for path_el in geom.findall(q('a:pathLst') + '/' + q('a:path')):
        pw = float(path_el.get('w') or w * EMU_PER_PX)
        ph_ = float(path_el.get('h') or h * EMU_PER_PX)
        sx = w / pw if pw else 1.0
        sy = h / ph_ if ph_ else 1.0

        def pt(el):
            return float(el.get('x')) * sx, float(el.get('y')) * sy

        d = []
        cur = (0.0, 0.0)
        for cmd in path_el:
            t = etree.QName(cmd).localname
            if t == 'moveTo':
                cur = pt(cmd[0])
                d.append(f'M {cur[0]:.2f} {cur[1]:.2f}')
            elif t == 'lnTo':
                cur = pt(cmd[0])
                d.append(f'L {cur[0]:.2f} {cur[1]:.2f}')
            elif t == 'cubicBezTo':
                pts = [pt(p_) for p_ in cmd]
                d.append('C ' + ' '.join(f'{x:.2f} {y:.2f}' for x, y in pts))
                cur = pts[-1]
            elif t == 'quadBezTo':
                pts = [pt(p_) for p_ in cmd]
                d.append('Q ' + ' '.join(f'{x:.2f} {y:.2f}' for x, y in pts))
                cur = pts[-1]
            elif t == 'arcTo':
                # approximate arc with a line to keep things simple
                wr = float(cmd.get('wR')) * sx
                hr = float(cmd.get('hR')) * sy
                st = float(cmd.get('stAng')) / 60000.0
                sw = float(cmd.get('swAng')) / 60000.0
                # current point lies at angle st on the ellipse; compute center
                a0 = math.radians(st)
                cx = cur[0] - wr * math.cos(a0)
                cy = cur[1] - hr * math.sin(a0)
                a1 = math.radians(st + sw)
                end = (cx + wr * math.cos(a1), cy + hr * math.sin(a1))
                large = 1 if abs(sw) > 180 else 0
                sweep = 1 if sw > 0 else 0
                d.append(f'A {wr:.2f} {hr:.2f} 0 {large} {sweep} {end[0]:.2f} {end[1]:.2f}')
                cur = end
            elif t == 'close':
                d.append('Z')
        paths.append(' '.join(d))
    return ' '.join(paths)


# ---------------------------------------------------------------- main converter


class Converter:
    def __init__(self, pptx_path, out_dir, pdf_path=None):
        self.pkg = Pkg(pptx_path)
        self.pdf = fitz.open(pdf_path) if pdf_path and os.path.exists(pdf_path) else None
        self._pdf_cache = {}
        self._current_page = None
        self.out_dir = out_dir
        self.img_dir = os.path.join(out_dir, 'img')
        os.makedirs(self.img_dir, exist_ok=True)
        self.media_cache = {}     # (part, variant) -> emitted filename
        self._hash_names = {}     # content sha1 -> emitted filename (dedup)
        self._used_names = {}     # filename -> content sha1 (collision check)
        self.warnings = []
        self._default_run_color = None
        self._svg_cache = {}      # svg asset file -> content

        pres = self.pkg.xml('ppt/presentation.xml')
        pres_rels = self.pkg.rels('ppt/presentation.xml')
        self.slide_parts = []
        for sld_id in pres.findall(q('p:sldIdLst') + '/' + q('p:sldId')):
            rid = sld_id.get(q('r:id'))
            self.slide_parts.append(pres_rels[rid][0])
        self.pres_default = pres.find(q('p:defaultTextStyle'))

    # -------- part helpers

    def layout_for(self, slide_part):
        for tgt, mode in self.pkg.rels(slide_part).values():
            if 'slideLayout' in tgt:
                return tgt
        return None

    def master_for(self, layout_part):
        for tgt, mode in self.pkg.rels(layout_part).values():
            if 'slideMaster' in tgt:
                return tgt
        return None

    def theme_for(self, master_part):
        for tgt, mode in self.pkg.rels(master_part).values():
            if 'theme' in tgt:
                return tgt
        return None

    def ctx_for(self, master_part):
        theme = self.pkg.xml(self.theme_for(master_part))
        scheme = theme.find(q('a:themeElements') + '/' + q('a:clrScheme'))
        colors = {}
        for ch in scheme:
            name = etree.QName(ch).localname
            sub = ch[0]
            if etree.QName(sub).localname == 'srgbClr':
                colors[name] = sub.get('val')
            else:
                colors[name] = sub.get('lastClr', '000000')
        fs = theme.find(q('a:themeElements') + '/' + q('a:fontScheme'))
        fonts = {
            'major': fs.find(q('a:majorFont') + '/' + q('a:latin')).get('typeface'),
            'minor': fs.find(q('a:minorFont') + '/' + q('a:latin')).get('typeface'),
        }
        master = self.pkg.xml(master_part)
        cm = master.find(q('p:clrMap'))
        clr_map = {k: cm.get(k) for k in ('bg1', 'tx1', 'bg2', 'tx2', 'accent1', 'accent2',
                                          'accent3', 'accent4', 'accent5', 'accent6',
                                          'hlink', 'folHlink')}
        return Ctx(colors, clr_map, fonts)

    # -------- media

    def _register(self, data, ext, slug):
        """Write image bytes once and return a stable, speaking file name.

        Identical content is de-duplicated to a single file; if two distinct
        images map to the same slug, later ones get a -2/-3 suffix.
        """
        h = hashlib.sha1(data).hexdigest()
        if h in self._hash_names:
            return self._hash_names[h]
        base = slug if slug else 'm' + h[:10]
        name = base + ext
        i = 2
        while name in self._used_names and self._used_names[name] != h:
            name = f'{base}-{i}{ext}'
            i += 1
        self._used_names[name] = h
        self._hash_names[h] = name
        path = os.path.join(self.img_dir, name)
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(data)
        return name

    def emit_media(self, media_part, variant='', transform=None):
        """Copy media into docs/img (dedup by content hash). transform: callable(Image)->Image."""
        key = (media_part, variant)
        if key in self.media_cache:
            return self.media_cache[key]
        if media_part in REPLACED_MEDIA:
            data = REPLACED_MEDIA[media_part]()
        else:
            data = self.pkg.read(media_part)
        ext = os.path.splitext(media_part)[1].lower()
        if ext == '.jfif':
            ext = '.jpeg'
        if transform is not None:
            im = Image.open(io.BytesIO(data)).convert('RGBA')
            im = transform(im)
            buf = io.BytesIO()
            im.save(buf, 'PNG')
            data = buf.getvalue()
            ext = '.png'
        slug = MEDIA_SLUGS.get((os.path.basename(media_part), variant))
        name = self._register(data, ext, slug)
        self.media_cache[key] = name
        return name

    # -------- placeholder lookup

    @staticmethod
    def find_ph(tree, ph_type, ph_idx):
        """Find placeholder sp in a layout/master spTree."""
        best = None
        for sp in tree.iter(q('p:sp')):
            ph = sp.find(q('p:nvSpPr') + '/' + q('p:nvPr') + '/' + q('p:ph'))
            if ph is None:
                continue
            t, i = ph.get('type'), ph.get('idx')
            if ph_idx is not None and i == ph_idx:
                return sp
            if ph_idx is None and i is None and _ph_type_match(t, ph_type):
                return sp
            if best is None and _ph_type_match(t, ph_type):
                best = sp
        return best

    # -------- animation

    def parse_animation(self, slide):
        """Return {spid: (click_index, stagger_step)}.

        click_index is 1-based click order (-> Reveal fragment index).
        stagger_step reproduces afterEffect chains inside one click as a
        CSS transition delay."""
        timing = slide.find(q('p:timing'))
        out = {}
        if timing is None:
            return out
        seq = timing.find('.//' + q('p:seq'))
        if seq is None:
            return out
        main_ctn = seq.find(q('p:cTn'))
        if main_ctn is None:
            return out
        child_lst = main_ctn.find(q('p:childTnLst'))
        if child_lst is None:
            return out
        click = 0
        for par in child_lst.findall(q('p:par')):
            click += 1
            step = 0
            first = True
            for ctn in par.iter(q('p:cTn')):
                node_type = ctn.get('nodeType')
                if node_type not in ('clickEffect', 'afterEffect', 'withEffect'):
                    continue
                if node_type == 'afterEffect' and not first:
                    step += 1
                first = False
                for tgt in ctn.iter(q('p:spTgt')):
                    spid = tgt.get('spid')
                    if spid is not None:
                        out.setdefault(spid, (click, step))
        return out

    # -------- conversion of one slide

    def convert_slide(self, slide_part, number):
        self._current_page = number
        slide = self.pkg.xml(slide_part)
        layout_part = self.layout_for(slide_part)
        layout = self.pkg.xml(layout_part)
        master_part = self.master_for(layout_part)
        master = self.pkg.xml(master_part)
        ctx = self.ctx_for(master_part)

        anim = self.parse_animation(slide)
        # spid -> fragment index for groups: propagate while walking

        parts = []

        # background
        bg_css = self.background_css(slide, layout, master, ctx, slide_part, layout_part, master_part)

        show_master_sp = layout.find(q('p:cSld')).getparent().get('showMasterSp', '1')
        if show_master_sp != '0':
            parts += self.walk_tree(master, master_part, ctx, layout, master,
                                    layout_part, master_part, anim={}, source='master')
        parts += self.walk_tree(layout, layout_part, ctx, layout, master,
                                layout_part, master_part, anim={}, source='layout')
        parts += self.walk_tree(slide, slide_part, ctx, layout, master,
                                layout_part, master_part, anim=anim, source='slide')

        notes_html = self.notes_html(slide_part, ctx)

        frag_count = len(set(anim.values()))
        body = '\n'.join(parts)
        style_bg = f' style="background:{bg_css};"' if bg_css else ''
        section = (f'<section data-pptx="{os.path.basename(slide_part)}" data-page="{number}">\n'
                   f'<div class="pcanvas"{style_bg}>\n{body}\n</div>\n'
                   f'{notes_html}\n</section>')
        return section

    def background_css(self, slide, layout, master, ctx, *parts_):
        for tree in (slide, layout, master):
            bg = tree.find(q('p:cSld') + '/' + q('p:bg'))
            if bg is None:
                continue
            bg_pr = bg.find(q('p:bgPr'))
            if bg_pr is not None:
                f = find_fill(bg_pr, ctx)
                if f is not None:
                    return fill_css(f, ctx)
            bg_ref = bg.find(q('p:bgRef'))
            if bg_ref is not None and len(bg_ref):
                return css_color(*resolve_color(bg_ref[0], ctx))
        return '#FFFFFF'

    # -------- shape tree walking

    def walk_tree(self, tree, part, ctx, layout, master, layout_part, master_part, anim, source):
        sp_tree = tree.find(q('p:cSld') + '/' + q('p:spTree'))
        out = []
        for child in sp_tree:
            out += self.walk_shape(child, part, ctx, layout, master, layout_part,
                                   master_part, anim, source,
                                   xform=None, frag=None)
        return out

    def walk_shape(self, el, part, ctx, layout, master, layout_part, master_part,
                   anim, source, xform, frag):
        tag = etree.QName(el).localname
        if tag == 'AlternateContent':
            # PowerPoint ink (p:contentPart, e.g. marker highlights) ships a
            # pre-rendered bitmap inside mc:Fallback — render those pics.
            # Highlighter ink (rasterOp=maskPen in the InkML brush) blends
            # with the text underneath instead of covering it.
            fb = el.find(q('mc:Fallback'))
            if fb is None:
                return []
            blend = ''
            cp = el.find(q('mc:Choice') + '/' + q('p:contentPart'))
            if cp is not None:
                rid = cp.get(q('r:id'))
                rels = self.pkg.rels(part)
                if rid in rels and b'maskPen' in self.pkg.read(rels[rid][0]):
                    blend = 'mix-blend-mode:multiply;'
            out = []
            for child in fb:
                if etree.QName(child).localname == 'pic':
                    out += self.render_pic(child, part, ctx, source, xform,
                                           frag, layout, master,
                                           extra_style=blend)
                else:
                    out += self.walk_shape(child, part, ctx, layout, master,
                                           layout_part, master_part, anim,
                                           source, xform, frag)
            return out
        if tag not in ('sp', 'pic', 'grpSp', 'graphicFrame', 'cxnSp'):
            return []
        spid = self._spid(el)
        frag_here = frag
        if spid in anim:
            frag_here = anim[spid]

        if tag == 'grpSp':
            return self.walk_group(el, part, ctx, layout, master, layout_part,
                                   master_part, anim, source, xform, frag_here)
        if tag == 'sp':
            return self.render_sp(el, part, ctx, layout, master, layout_part,
                                  master_part, source, xform, frag_here)
        if tag == 'cxnSp':
            return self.render_cxn(el, part, ctx, xform, frag_here)
        if tag == 'pic':
            return self.render_pic(el, part, ctx, source, xform, frag_here,
                                   layout, master)
        if tag == 'graphicFrame':
            return self.render_graphic_frame(el, part, ctx, xform, frag_here)
        return []

    @staticmethod
    def _spid(el):
        for nv in el:
            if etree.QName(nv).localname.startswith('nv'):
                c = nv.find(q('p:cNvPr'))
                if c is not None:
                    return c.get('id')
        return None

    @staticmethod
    def _name(el):
        for nv in el:
            if etree.QName(nv).localname.startswith('nv'):
                c = nv.find(q('p:cNvPr'))
                if c is not None:
                    return c.get('name') or ''
        return ''

    def get_xfrm(self, el):
        """Return (x, y, w, h, rot_deg, flipH, flipV) in EMU or None."""
        sp_pr = None
        for cand in (q('p:spPr'), q('p:grpSpPr')):
            sp_pr = el.find(cand)
            if sp_pr is not None:
                break
        if sp_pr is None and etree.QName(el).localname == 'graphicFrame':
            xfrm = el.find(q('p:xfrm'))
        else:
            xfrm = sp_pr.find(q('a:xfrm')) if sp_pr is not None else None
        if xfrm is None:
            return None
        off = xfrm.find(q('a:off'))
        ext = xfrm.find(q('a:ext'))
        if off is None or ext is None:
            return None
        return {
            'x': float(off.get('x')), 'y': float(off.get('y')),
            'w': float(ext.get('cx')), 'h': float(ext.get('cy')),
            'rot': float(xfrm.get('rot', '0')) / 60000.0,
            'flipH': xfrm.get('flipH') == '1',
            'flipV': xfrm.get('flipV') == '1',
        }

    @staticmethod
    def apply_xform(geo, xform):
        if xform is None:
            return geo
        g = dict(geo)
        g['x'] = xform['ox'] + (geo['x'] - xform['chx']) * xform['sx']
        g['y'] = xform['oy'] + (geo['y'] - xform['chy']) * xform['sy']
        g['w'] = geo['w'] * xform['sx']
        g['h'] = geo['h'] * xform['sy']
        if xform.get('flipH'):
            # mirror inside group bounds
            g['x'] = 2 * xform['ox'] + xform['gw'] - g['x'] - g['w']
            g['flipH'] = not g.get('flipH', False)
        if xform.get('flipV'):
            g['y'] = 2 * xform['oy'] + xform['gh'] - g['y'] - g['h']
            g['flipV'] = not g.get('flipV', False)
        return g

    @staticmethod
    def off_canvas(geo):
        x, y = emu2px(geo['x']), emu2px(geo['y'])
        w, h = emu2px(geo['w']), emu2px(geo['h'])
        return x + w <= 0 or y + h <= 0 or x >= 960 or y >= 540

    def walk_group(self, grp, part, ctx, layout, master, layout_part, master_part,
                   anim, source, xform, frag):
        geo = self.get_xfrm(grp)
        if geo is None:
            return []
        geo_abs = self.apply_xform(geo, xform)
        gsp_pr = grp.find(q('p:grpSpPr'))
        xfrm = gsp_pr.find(q('a:xfrm'))
        ch_off = xfrm.find(q('a:chOff'))
        ch_ext = xfrm.find(q('a:chExt'))
        chx = float(ch_off.get('x')) if ch_off is not None else geo['x']
        chy = float(ch_off.get('y')) if ch_off is not None else geo['y']
        chw = float(ch_ext.get('cx')) if ch_ext is not None else geo['w']
        chh = float(ch_ext.get('cy')) if ch_ext is not None else geo['h']
        rotated = bool(geo['rot']) or geo['flipH'] or geo['flipV']
        new_xform = {
            # rotated groups become a wrapper div; children are positioned
            # group-locally so the wrapper's CSS transform applies to all
            'ox': 0.0 if rotated else geo_abs['x'],
            'oy': 0.0 if rotated else geo_abs['y'],
            'chx': chx, 'chy': chy,
            'sx': geo_abs['w'] / chw if chw else 1.0,
            'sy': geo_abs['h'] / chh if chh else 1.0,
            'gw': geo_abs['w'], 'gh': geo_abs['h'],
            'flipH': False, 'flipV': False,
        }
        out = []
        for child in grp:
            out += self.walk_shape(child, part, ctx, layout, master, layout_part,
                                   master_part, anim, source, new_xform,
                                   frag if not rotated else None)
        if rotated:
            cls = 'grp' + self.frag_class(frag)
            style = 'position:absolute;' + self.pos_css(geo_abs) + self.frag_style(frag)
            return [f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>\n'
                    + '\n'.join(out) + '\n</div>']
        return out

    # -------- common css

    @staticmethod
    def pos_css(geo):
        x, y = emu2px(geo['x']), emu2px(geo['y'])
        w, h = emu2px(geo['w']), emu2px(geo['h'])
        css = f'left:{fmt(x)}px;top:{fmt(y)}px;width:{fmt(w)}px;height:{fmt(h)}px;'
        tr = []
        if geo.get('rot'):
            tr.append(f'rotate({geo["rot"]:.2f}deg)')
        if geo.get('flipH'):
            tr.append('scaleX(-1)')
        if geo.get('flipV'):
            tr.append('scaleY(-1)')
        if tr:
            css += f'transform:{" ".join(tr)};'
        return css

    @staticmethod
    def frag_attr(frag):
        if frag is None:
            return ''
        return f' data-fragment-index="{frag[0] - 1}"'

    @staticmethod
    def frag_class(frag):
        return ' fragment' if frag is not None else ''

    @staticmethod
    def frag_style(frag):
        """Stagger afterEffect chains that share one click."""
        if frag is None or frag[1] == 0:
            return ''
        return f'transition-delay:{frag[1] * 0.4:.1f}s;'

    def shadow_css(self, sp_pr, ctx, kind='box'):
        if sp_pr is None:
            return ''
        shdw = sp_pr.find(q('a:effectLst') + '/' + q('a:outerShdw'))
        if shdw is None:
            return ''
        blur = emu2px(float(shdw.get('blurRad', '0')))
        dist = emu2px(float(shdw.get('dist', '0')))
        ang = float(shdw.get('dir', '0')) / 60000.0
        dx = dist * math.cos(math.radians(ang))
        dy = dist * math.sin(math.radians(ang))
        if len(shdw):
            hexv, alpha = resolve_color(shdw[0], ctx)
            # CSS shadows draw noticeably heavier than PowerPoint's at equal alpha
            col = css_color(hexv, alpha * 0.55)
        else:
            col = 'rgba(0,0,0,.25)'
        if kind == 'drop':
            return f'filter:drop-shadow({fmt(dx)}px {fmt(dy)}px {fmt(blur / 2)}px {col});'
        return f'box-shadow:{fmt(dx)}px {fmt(dy)}px {fmt(blur)}px {col};'

    def line_css(self, sp_pr, ctx):
        ln = sp_pr.find(q('a:ln')) if sp_pr is not None else None
        if ln is None:
            return ''
        if ln.find(q('a:noFill')) is not None:
            return ''
        f = None
        for ch in ln:
            if etree.QName(ch).localname in ('solidFill', 'gradFill'):
                f = ch
                break
        if f is None:
            return ''
        w = emu2px(float(ln.get('w', '9525')))
        col = fill_css(f, ctx)
        return f'border:{fmt(max(w, 0.5))}px solid {col};'

    # -------- sp rendering

    def render_sp(self, sp, part, ctx, layout, master, layout_part, master_part,
                  source, xform, frag):
        ph = sp.find(q('p:nvSpPr') + '/' + q('p:nvPr') + '/' + q('p:ph'))
        ph_type = ph.get('type') if ph is not None else None
        ph_idx = ph.get('idx') if ph is not None else None

        # skip housekeeping placeholders everywhere
        if ph_type in ('sldNum', 'dt', 'ftr'):
            return []
        # layout/master placeholders are prompts/slots, never rendered content
        if source in ('layout', 'master') and ph is not None:
            return []

        # banned text filter
        all_text = ' '.join(t.text or '' for t in sp.iter(q('a:t')))
        for pat, repl in TEXT_REPLACEMENTS:
            all_text = pat.sub(repl, all_text)
        if BANNED_RE.search(all_text):
            return []

        layout_ph = master_ph = None
        if ph is not None:
            layout_ph = self.find_ph(layout, ph_type, ph_idx)
            master_ph = self.find_ph(master, ph_type, ph_idx)

        geo = self.get_xfrm(sp)
        if geo is None:
            for cand in (layout_ph, master_ph):
                if cand is not None:
                    geo = self.get_xfrm(cand)
                    if geo is not None:
                        break
        if geo is None:
            self.warnings.append(f'no geometry for shape "{self._name(sp)}" in {part}')
            return []
        geo = self.apply_xform(geo, xform)

        sp_pr = sp.find(q('p:spPr'))
        geom_el = sp_pr.find(q('a:prstGeom')) if sp_pr is not None else None
        cust_el = sp_pr.find(q('a:custGeom')) if sp_pr is not None else None
        prst = geom_el.get('prst') if geom_el is not None else None

        fill_el = find_fill(sp_pr, ctx)
        # placeholder fill inheritance
        if fill_el is None and ph is not None:
            for cand in (layout_ph, master_ph):
                if cand is not None:
                    fill_el = find_fill(cand.find(q('p:spPr')), ctx)
                    if fill_el is not None:
                        break
        geo_w, geo_h = emu2px(geo['w']), emu2px(geo['h'])
        bg = (fill_css(fill_el, ctx, geo_w, geo_h)
              if fill_el is not None and etree.QName(fill_el).localname != 'blipFill' else None)

        # theme style references (p:style) act as defaults
        style_el = sp.find(q('p:style'))
        default_color = None
        if style_el is not None:
            if bg is None and fill_el is None:
                fill_ref = style_el.find(q('a:fillRef'))
                if fill_ref is not None and fill_ref.get('idx', '0') not in ('0', ''):
                    if len(fill_ref):
                        bg = css_color(*resolve_color(fill_ref[0], ctx))
            font_ref = style_el.find(q('a:fontRef'))
            if font_ref is not None and len(font_ref):
                default_color = css_color(*resolve_color(font_ref[0], ctx))

        txbody = sp.find(q('p:txBody'))
        text_html = ''
        if txbody is not None:
            self._default_run_color = default_color
            text_html = self.text_html(txbody, ctx, ph, layout_ph, master_ph, master)
            self._default_run_color = None

        w, h = emu2px(geo['w']), emu2px(geo['h'])

        if source in ('layout', 'master') and self.off_canvas(geo):
            return []

        cls = 'shp' + self.frag_class(frag)
        style = 'position:absolute;' + self.pos_css(geo) + self.frag_style(frag)
        style += self.shadow_css(sp_pr, ctx, kind='box' if prst in (None, 'rect', 'roundRect') else 'drop')
        z = SHAPE_Z_OVERRIDES.get((os.path.basename(part), self._name(sp)))
        if z is not None:
            style += f'z-index:{z};'

        if prst in ('line', 'straightConnector1') and (w < 1 or h < 1):
            return self.axis_line_div(geo, sp_pr.find(q('a:ln')) if sp_pr is not None else None,
                                      ctx, cls, frag)

        if cust_el is not None or prst in ('leftBrace', 'rightBrace', 'line', 'straightConnector1'):
            svg_inner = self.shape_svg(sp_pr, prst, cust_el, w, h, ctx)
            return [f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>{svg_inner}{text_html}</div>']

        if prst == 'ellipse':
            style += 'border-radius:50%;'
        elif prst == 'roundRect':
            adj = 0.16667
            avLst = geom_el.find(q('a:avLst'))
            if avLst is not None:
                gd = avLst.find(q('a:gd'))
                if gd is not None and gd.get('fmla', '').startswith('val '):
                    adj = float(gd.get('fmla').split()[1]) / 100000
            style += f'border-radius:{fmt(adj * min(w, h))}px;'
        if bg:
            style += f'background:{bg};'
        border = self.line_css(sp_pr, ctx)
        if not border and style_el is not None and (sp_pr is None or sp_pr.find(q('a:ln')) is None):
            ln_ref = style_el.find(q('a:lnRef'))
            if ln_ref is not None and ln_ref.get('idx', '0') not in ('0', '') and len(ln_ref):
                border = f'border:1px solid {css_color(*resolve_color(ln_ref[0], ctx))};'
        style += border
        return [f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>{text_html}</div>']

    _svg_grad_n = 0

    def stroke_paint(self, ln, ctx):
        """Resolve an a:ln to (svg_stroke, svg_defs)."""
        stroke, defs = 'none', ''
        if ln is None:
            return stroke, defs
        for ch in ln:
            t = etree.QName(ch).localname
            if t == 'solidFill':
                stroke = css_color(*resolve_color(ch[0], ctx))
            elif t == 'gradFill':
                Converter._svg_grad_n += 1
                gid = f'lngrad{Converter._svg_grad_n}'
                stops = []
                for gs in ch.findall(q('a:gsLst') + '/' + q('a:gs')):
                    pos = int(gs.get('pos')) / 1000
                    hexv, alpha = resolve_color(gs[0], ctx)
                    stops.append(f'<stop offset="{pos:.1f}%" stop-color="#{hexv}" '
                                 f'stop-opacity="{alpha:.3f}"/>')
                lin = ch.find(q('a:lin'))
                ang = int(lin.get('ang', '0')) / 60000.0 if lin is not None else 0.0
                rad = math.radians(ang)
                x2, y2 = math.cos(rad), math.sin(rad)
                defs = (f'<defs><linearGradient id="{gid}" x1="0" y1="0" '
                        f'x2="{abs(x2):.3f}" y2="{abs(y2):.3f}">{"".join(stops)}'
                        f'</linearGradient></defs>')
                stroke = f'url(#{gid})'
        return stroke, defs

    def axis_line_div(self, geo, ln, ctx, cls, frag):
        """Horizontal/vertical lines as divs — SVG strokes with a degenerate
        bounding box can't carry gradients and scale badly."""
        w, h = emu2px(geo['w']), emu2px(geo['h'])
        stroke_w = emu2px(float(ln.get('w', '9525'))) if ln is not None else 1.0
        bg = None
        if ln is not None:
            for ch in ln:
                t = etree.QName(ch).localname
                if t == 'solidFill':
                    bg = css_color(*resolve_color(ch[0], ctx))
                elif t == 'gradFill':
                    bg = fill_css(ch, ctx, max(w, 1), max(h, 1))
        if bg is None:
            bg = '#1B1B1B'
        g = dict(geo)
        if w >= h:  # horizontal
            g['y'] -= stroke_w / 2 * EMU_PER_PX
            g['h'] = stroke_w * EMU_PER_PX
        else:
            g['x'] -= stroke_w / 2 * EMU_PER_PX
            g['w'] = stroke_w * EMU_PER_PX
        style = ('position:absolute;' + self.pos_css(g)
                 + f'background:{bg};' + self.frag_style(frag))
        return [f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}></div>']

    def shape_svg(self, sp_pr, prst, cust_el, w, h, ctx):
        ln = sp_pr.find(q('a:ln')) if sp_pr is not None else None
        stroke_w = 1.0
        stroke, defs = self.stroke_paint(ln, ctx)
        if ln is not None:
            stroke_w = emu2px(float(ln.get('w', '9525')))
        fill_el = find_fill(sp_pr, ctx)
        fill = 'none'
        if fill_el is not None and etree.QName(fill_el).localname == 'solidFill':
            fill = css_color(*resolve_color(fill_el[0], ctx))
        if cust_el is not None:
            d = custgeom_svg_path(cust_el, w, h)
            if fill_el is None:
                fill = 'none'
        elif prst in ('leftBrace', 'rightBrace'):
            d = brace_path(w, h, left=(prst == 'leftBrace'))
            fill = 'none'
            if stroke == 'none':
                stroke = '#1B1B1B'
        else:  # line / straightConnector1
            d = f'M 0 0 L {w:.1f} {h:.1f}'
            if stroke == 'none' and not defs:
                stroke = '#1B1B1B'
        return (f'<svg width="{fmt(w)}" height="{fmt(h)}" viewBox="0 0 {fmt(w)} {fmt(h)}" '
                f'style="position:absolute;left:0;top:0;overflow:visible;">{defs}'
                f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{fmt(stroke_w)}" '
                f'stroke-linecap="round" stroke-linejoin="round"/></svg>')

    # -------- connectors

    def render_cxn(self, cxn, part, ctx, xform, frag):
        geo = self.get_xfrm(cxn)
        if geo is None:
            return []
        geo = self.apply_xform(geo, xform)
        sp_pr = cxn.find(q('p:spPr'))
        w, h = max(emu2px(geo['w']), 0.1), max(emu2px(geo['h']), 0.1)
        ln = sp_pr.find(q('a:ln'))
        w0, h0 = emu2px(geo['w']), emu2px(geo['h'])
        if (w0 < 1 or h0 < 1) and (ln is None or
                (ln.find(q('a:headEnd')) is None or ln.find(q('a:headEnd')).get('type', 'none') == 'none') and
                (ln.find(q('a:tailEnd')) is None or ln.find(q('a:tailEnd')).get('type', 'none') == 'none')):
            return self.axis_line_div(geo, ln, ctx, 'shp' + self.frag_class(frag), frag)
        stroke_w = 1.5
        head = tail = None
        stroke, defs = self.stroke_paint(ln, ctx)
        if stroke == 'none' and not defs:
            stroke = '#1B1B1B'
        if ln is not None:
            for ch in ln:
                t = etree.QName(ch).localname
                if t == 'headEnd':
                    head = ch.get('type', 'none')
                elif t == 'tailEnd':
                    tail = ch.get('type', 'none')
            stroke_w = emu2px(float(ln.get('w', '12700')))
        x1, y1, x2, y2 = 0, 0, w, h
        if geo.get('flipH'):
            x1, x2 = w, 0
        if geo.get('flipV'):
            y1, y2 = h, 0
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        s = max(stroke_w * 3, 6)

        def arrow(x, y, a):
            return (f'<path d="M {x - s:.1f} {-s / 2:.1f} L 0 0 L {x - s:.1f} {s / 2:.1f}" '
                    f'transform="translate({x:.1f},{y:.1f}) rotate({a:.1f}) translate({-x:.1f},{-y:.1f})" '
                    f'fill="none" stroke="{stroke}" stroke-width="{fmt(stroke_w)}" '
                    f'stroke-linecap="round"/>')

        inner = (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{fmt(stroke_w)}"/>')
        if tail and tail != 'none':
            a = ang
            inner += (f'<path d="M -{s:.1f} -{s / 2:.1f} L 0 0 L -{s:.1f} {s / 2:.1f}" fill="none" '
                      f'stroke="{stroke}" stroke-width="{fmt(stroke_w)}" stroke-linecap="round" '
                      f'transform="translate({x2:.1f},{y2:.1f}) rotate({a:.1f})"/>')
        if head and head != 'none':
            a = ang + 180
            inner += (f'<path d="M -{s:.1f} -{s / 2:.1f} L 0 0 L -{s:.1f} {s / 2:.1f}" fill="none" '
                      f'stroke="{stroke}" stroke-width="{fmt(stroke_w)}" stroke-linecap="round" '
                      f'transform="translate({x1:.1f},{y1:.1f}) rotate({a:.1f})"/>')
        cls = 'shp' + self.frag_class(frag)
        geo2 = dict(geo)
        geo2['flipH'] = geo2['flipV'] = False  # baked into coords
        style = 'position:absolute;' + self.pos_css(geo2) + self.frag_style(frag)
        svg = (f'<svg width="{fmt(w)}" height="{fmt(h)}" viewBox="0 0 {fmt(w)} {fmt(h)}" '
               f'style="position:absolute;left:0;top:0;overflow:visible;">{defs}{inner}</svg>')
        return [f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>{svg}</div>']

    # -------- pictures

    def render_pic(self, pic, part, ctx, source, xform, frag,
                   layout=None, master=None, extra_style=''):
        blip_fill = pic.find(q('p:blipFill'))
        blip = blip_fill.find(q('a:blip')) if blip_fill is not None else None
        if blip is None:
            return []
        rid = blip.get(q('r:embed'))
        rels = self.pkg.rels(part)
        if rid not in rels:
            return []
        media_part = rels[rid][0]
        if media_part in BANNED_MEDIA or media_part in SKIPPED_INK_MEDIA:
            return []
        geo = self.get_xfrm(pic)
        if geo is None:
            # picture placeholders inherit their frame from the layout/master
            ph = pic.find(q('p:nvPicPr') + '/' + q('p:nvPr') + '/' + q('p:ph'))
            if ph is not None:
                for tree in (layout, master):
                    if tree is None:
                        continue
                    cand = self.find_ph(tree, ph.get('type'), ph.get('idx'))
                    if cand is not None:
                        geo = self.get_xfrm(cand)
                        if geo is not None:
                            break
        if geo is None:
            return []
        geo = self.apply_xform(geo, xform)
        if source in ('layout', 'master') and self.off_canvas(geo):
            return []

        # the title-slide background is replaced by an inline animated SVG
        if media_part == TITLE_BG_MEDIA:
            cls = 'pic' + self.frag_class(frag)
            style = 'position:absolute;' + self.pos_css(geo)
            return [f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>'
                    f'{_title_bg_svg()}</div>']

        # PowerPoint background removal cannot be recomputed — pull the
        # processed bitmap (incl. baked duotone) out of the rendered PDF
        if blip.find(f'.//{{{A14_NS}}}backgroundRemoval') is not None:
            fname = self.extract_from_pdf(geo)
            if fname:
                geo = self._apply_pos_override(part, fname, geo)
                return self.emit_pic_html(pic, blip_fill, geo, ctx, frag, fname, '',
                                          from_pdf=True)
            self.warnings.append(f'backgroundRemoval not matched in PDF for {part} page {self._current_page}')

        # color effects on the blip
        transform = None
        variant = ''
        duo = blip.find(q('a:duotone'))
        if duo is not None and len(duo) >= 2:
            c1 = resolve_color(duo[0], ctx)[0]
            c2 = resolve_color(duo[1], ctx)[0]
            variant = f'duo{c1}{c2}'

            def transform(im, c1=c1, c2=c2):
                rgb1 = tuple(int(c1[i:i + 2], 16) for i in (0, 2, 4))
                rgb2 = tuple(int(c2[i:i + 2], 16) for i in (0, 2, 4))
                g = im.convert('L')
                bands = [g.point([int(rgb1[b] + (rgb2[b] - rgb1[b]) * (v / 255)) for v in range(256)])
                         for b in range(3)]
                out = Image.merge('RGB', bands)
                out.putalpha(im.getchannel('A'))
                return out
        gray_el = blip.find(q('a:grayscl'))
        if gray_el is not None:
            variant = 'gray'

            def transform(im):
                g = im.convert('L').convert('RGB')
                g.putalpha(im.getchannel('A'))
                return g
        alpha_mod = blip.find(q('a:alphaModFix'))
        opacity = ''
        if alpha_mod is not None:
            amt = int(alpha_mod.get('amt', '100000')) / 100000
            opacity = f'opacity:{amt:.3f};'

        fname = self.emit_media(media_part, variant, transform)
        geo = self._apply_pos_override(part, fname, geo)
        return self.emit_pic_html(pic, blip_fill, geo, ctx, frag, fname,
                                  opacity + extra_style)

    @staticmethod
    def _apply_pos_override(part, fname, geo):
        override = PIC_POS_OVERRIDES.get((os.path.basename(part), fname))
        if override is not None:
            geo = dict(geo)
            geo['x'] = override[0] * EMU_PER_PX
            geo['y'] = override[1] * EMU_PER_PX
        return geo

    def inline_svg(self, fname, img_style):
        """Inline the hand-drawn SVG replacing docs/img/<fname>, or None.

        The SVG root gets the same CSS placement the <img> would have had;
        a fit box rewraps the artwork into the padded canvas of the replaced
        bitmap so on-slide size and position stay identical."""
        entry = SVG_REPLACEMENTS.get(fname)
        if entry is None:
            return None
        svg_file, fit = entry
        if svg_file not in self._svg_cache:
            with open(os.path.join(SVG_ASSETS_DIR, svg_file)) as f:
                content = f.read().strip()
            content = re.sub(r'<\?xml[^>]*\?>\s*', '', content)
            self._svg_cache[svg_file] = content
        content = self._svg_cache[svg_file]
        if fit is not None:
            m = re.match(r'<svg([^>]*)>(.*)</svg>\s*$', content, re.S)
            attrs, inner = m.group(1), m.group(2)
            vb = re.search(r'viewBox="([^"]+)"', attrs).group(1)
            x0, y0, x1, y1 = fit
            return (f'<svg viewBox="0 0 100 100" style="{img_style}">'
                    f'<svg x="{fmt(x0 * 100)}" y="{fmt(y0 * 100)}"'
                    f' width="{fmt((x1 - x0) * 100)}" height="{fmt((y1 - y0) * 100)}"'
                    f' viewBox="{vb}" preserveAspectRatio="xMidYMid meet">'
                    f'{inner}</svg></svg>')
        return content.replace('<svg ', f'<svg style="{img_style}" ', 1)

    def emit_pic_html(self, pic, blip_fill, geo, ctx, frag, fname, opacity,
                      from_pdf=False):
        w, h = emu2px(geo['w']), emu2px(geo['h'])
        # bitmaps lifted from the PDF are already cropped to their placement
        src = None if from_pdf else blip_fill.find(q('a:srcRect'))
        img_style = 'position:absolute;left:0;top:0;width:100%;height:100%;'
        if src is not None:
            l = int(src.get('l', '0')) / 100000
            t = int(src.get('t', '0')) / 100000
            r_ = int(src.get('r', '0')) / 100000
            b = int(src.get('b', '0')) / 100000
            fx = max(1 - l - r_, 1e-6)
            fy = max(1 - t - b, 1e-6)
            img_style = (f'position:absolute;'
                         f'left:{fmt(-l / fx * 100)}%;top:{fmt(-t / fy * 100)}%;'
                         f'width:{fmt(100 / fx)}%;height:{fmt(100 / fy)}%;')

        sp_pr = pic.find(q('p:spPr'))
        radius = ''
        geom_el = sp_pr.find(q('a:prstGeom')) if sp_pr is not None else None
        if geom_el is not None and geom_el.get('prst') == 'ellipse':
            radius = 'border-radius:50%;'
        elif geom_el is not None and geom_el.get('prst') == 'roundRect':
            radius = f'border-radius:{fmt(0.16667 * min(w, h))}px;'

        shadow = self.shadow_css(sp_pr, ctx, kind='drop')
        cls = 'pic' + self.frag_class(frag)
        svg = self.inline_svg(fname, img_style)
        if svg is not None:
            # the flat SVG style bans shadows — drop the PPTX picture shadow
            style = ('position:absolute;' + self.pos_css(geo) + opacity
                     + self.frag_style(frag))
            return [(f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>'
                     f'<div data-svg-replaced="{fname}"'
                     f' style="position:absolute;inset:0;overflow:hidden;{radius}">'
                     f'{svg}</div></div>')]
        style = ('position:absolute;' + self.pos_css(geo) + shadow + opacity
                 + self.frag_style(frag))
        return [(f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>'
                 f'<div style="position:absolute;inset:0;overflow:hidden;{radius}">'
                 f'<img src="img/{fname}" style="{img_style}" alt=""></div></div>')]

    def extract_from_pdf(self, geo):
        """Find the bitmap drawn at geo's position on the current PDF page and
        emit it (with its soft-mask alpha) as a PNG. Returns filename or None."""
        if self.pdf is None or self._current_page is None:
            return None
        page = self.pdf[self._current_page - 1]
        # target rect in PDF points (page is 720x405pt for a 960x540px slide)
        scale = page.rect.width / 960.0
        tx0 = emu2px(geo['x']) * scale
        ty0 = emu2px(geo['y']) * scale
        tx1 = tx0 + emu2px(geo['w']) * scale
        ty1 = ty0 + emu2px(geo['h']) * scale
        target = fitz.Rect(tx0, ty0, tx1, ty1)
        best = (0.4, None)  # require decent overlap
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                inter = fitz.Rect(r) & target
                union_area = r.get_area() + target.get_area() - inter.get_area()
                iou = inter.get_area() / union_area if union_area else 0
                if iou > best[0]:
                    best = (iou, img)
        if best[1] is None:
            return None
        xref, smask = best[1][0], best[1][1]
        key = (self._current_page, xref)
        if key in self._pdf_cache:
            return self._pdf_cache[key]
        pix = fitz.Pixmap(self.pdf, xref)
        if pix.colorspace is None or pix.colorspace.n > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        if pix.alpha:
            pix = fitz.Pixmap(pix, 0)  # smask combination needs alpha-free base
        if smask:
            pix = fitz.Pixmap(pix, fitz.Pixmap(self.pdf, smask))
        data = pix.tobytes('png')
        slug = PDF_SLUGS.get(f'{self._current_page}x{xref}')
        name = self._register(data, '.png', slug)
        self._pdf_cache[key] = name
        return name

    # -------- tables

    def render_graphic_frame(self, gf, part, ctx, xform, frag):
        tbl = gf.find('.//' + q('a:tbl'))
        if tbl is None:
            return self.render_smartart(gf, part, ctx, xform, frag)
        geo = self.get_xfrm(gf)
        if geo is None:
            return []
        geo = self.apply_xform(geo, xform)
        cols = [emu2px(float(gc.get('w'))) for gc in tbl.findall(q('a:tblGrid') + '/' + q('a:gridCol'))]
        rows_html = []
        for tr in tbl.findall(q('a:tr')):
            rh = emu2px(float(tr.get('h')))
            cells = []
            ci = 0
            for tc in tr.findall(q('a:tc')):
                if tc.get('hMerge') == '1' or tc.get('vMerge') == '1':
                    ci += 1
                    continue
                span = int(tc.get('gridSpan', '1'))
                rspan = int(tc.get('rowSpan', '1'))
                tc_pr = tc.find(q('a:tcPr'))
                cell_style = 'vertical-align:middle;'
                if tc_pr is not None:
                    f = find_fill(tc_pr, ctx)
                    if f is not None:
                        bgc = fill_css(f, ctx)
                        if bgc:
                            cell_style += f'background:{bgc};'
                    for side, css_side in (('lnL', 'border-left'), ('lnR', 'border-right'),
                                           ('lnT', 'border-top'), ('lnB', 'border-bottom')):
                        ln = tc_pr.find(q(f'a:{side}'))
                        if ln is not None:
                            sf = None
                            for ch in ln:
                                if etree.QName(ch).localname == 'solidFill':
                                    sf = ch
                            if sf is not None:
                                lw = emu2px(float(ln.get('w', '9525')))
                                cell_style += f'{css_side}:{fmt(max(lw, 0.5))}px solid {css_color(*resolve_color(sf[0], ctx))};'
                txt = self.text_html(tc.find(q('a:txBody')), ctx, None, None, None, None, table_cell=True)
                attrs = ''
                if span > 1:
                    attrs += f' colspan="{span}"'
                if rspan > 1:
                    attrs += f' rowspan="{rspan}"'
                cells.append(f'<td style="{cell_style}"{attrs}>{txt}</td>')
                ci += span
            rows_html.append(f'<tr style="height:{fmt(rh)}px;">{"".join(cells)}</tr>')
        cls = 'tblw' + self.frag_class(frag)
        style = 'position:absolute;' + self.pos_css(geo) + self.frag_style(frag)
        colgroup = ''.join(f'<col style="width:{fmt(c)}px;">' for c in cols)
        return [(f'<div class="{cls}" style="{style}"{self.frag_attr(frag)}>'
                 f'<table class="ptbl"><colgroup>{colgroup}</colgroup>{"".join(rows_html)}</table></div>')]

    # -------- SmartArt

    DGM_NS = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'
    DSP_NS = 'http://schemas.microsoft.com/office/drawing/2008/diagram'

    def render_smartart(self, gf, part, ctx, xform, frag):
        """Render a SmartArt diagram from its pre-laid-out drawing part.

        PowerPoint stores the resolved shapes (dsp:sp) in ppt/diagrams/
        drawingN.xml; coordinates there are frame-local EMU.
        """
        rel_ids = gf.find('.//' + f'{{{self.DGM_NS}}}relIds')
        if rel_ids is None:
            self.warnings.append(f'unsupported graphicFrame in {part}')
            return []
        geo = self.get_xfrm(gf)
        if geo is None:
            return []
        geo = self.apply_xform(geo, xform)
        rels = self.pkg.rels(part)
        dm = rel_ids.get(q('r:dm'))
        if dm not in rels:
            return []
        data_part = rels[dm][0]
        drawing_part = None
        for source_rels in (rels, self.pkg.rels(data_part)):
            for tgt, mode in source_rels.values():
                if 'diagrams/drawing' in tgt:
                    drawing_part = tgt
        if drawing_part is None:
            self.warnings.append(f'SmartArt without drawing part in {part}')
            return []
        # re-bind the dsp namespace to the presentationml namespace so the
        # resolved shapes can be fed through the regular sp renderer
        raw = self.pkg.read(drawing_part).replace(
            self.DSP_NS.encode(), NS['p'].encode())
        drawing = etree.fromstring(raw)
        sp_tree = drawing.find(q('p:spTree'))
        if sp_tree is None:
            return []
        local_xform = {
            'ox': geo['x'], 'oy': geo['y'], 'chx': 0.0, 'chy': 0.0,
            'sx': 1.0, 'sy': 1.0, 'gw': geo['w'], 'gh': geo['h'],
            'flipH': False, 'flipV': False,
        }
        out = []
        for sp in sp_tree.findall(q('p:sp')):
            out += self.render_sp(sp, part, ctx, None, None, None, None,
                                  'slide', local_xform, frag)
        return out

    # -------- text

    def text_html(self, txbody, ctx, ph, layout_ph, master_ph, master, table_cell=False):
        if txbody is None:
            return ''
        body_pr = txbody.find(q('a:bodyPr'))
        # inherit bodyPr from placeholder chain
        anchors = []
        for el in (body_pr,):
            if el is not None and el.get('anchor'):
                anchors.append(el.get('anchor'))
        for cand in (layout_ph, master_ph):
            if cand is not None:
                bp = cand.find(q('p:txBody') + '/' + q('a:bodyPr'))
                if bp is not None and bp.get('anchor'):
                    anchors.append(bp.get('anchor'))
        anchor = anchors[0] if anchors else 't'
        justify = {'t': 'flex-start', 'ctr': 'center', 'b': 'flex-end'}.get(anchor, 'flex-start')

        ins = {}
        for k, dflt in (('lIns', 91440), ('rIns', 91440), ('tIns', 45720), ('bIns', 45720)):
            v = dflt
            if body_pr is not None and body_pr.get(k):
                v = int(body_pr.get(k))
            ins[k] = emu2px(v)

        font_scale = 1.0
        lnspc_red = 0.0
        for el in [body_pr] + [c.find(q('p:txBody') + '/' + q('a:bodyPr')) for c in (layout_ph, master_ph) if c is not None]:
            if el is None:
                continue
            na = el.find(q('a:normAutofit'))
            if na is not None:
                font_scale = int(na.get('fontScale', '100000')) / 100000
                lnspc_red = int(na.get('lnSpcReduction', '0')) / 100000
                break

        wrap = body_pr.get('wrap') if body_pr is not None else None

        sources = style_sources(txbody, ph, layout_ph, master_ph, master, self.pres_default)

        paras = txbody.findall(q('a:p'))
        out = []
        autonum_counters = {}
        for p in paras:
            out.append(self.para_html(p, sources, ctx, font_scale, lnspc_red, autonum_counters))
        pad = f'padding:{fmt(ins["tIns"])}px {fmt(ins["rIns"])}px {fmt(ins["bIns"])}px {fmt(ins["lIns"])}px;'
        nowrap = 'white-space:nowrap;' if wrap == 'none' else ''
        if table_cell:
            return f'<div class="tx" style="position:relative;display:block;{pad}{nowrap}">{"".join(out)}</div>'
        return (f'<div class="tx" style="position:absolute;inset:0;display:flex;flex-direction:column;'
                f'justify-content:{justify};{pad}{nowrap}">{"".join(out)}</div>')

    def para_html(self, p, sources, ctx, font_scale, lnspc_red, autonum_counters):
        ppr = p.find(q('a:pPr'))
        lvl = int(ppr.get('lvl', '0')) if ppr is not None else 0
        cands = lvl_candidates(sources, lvl)
        # a paragraph's own pPr/defRPr beats the inherited level styles for runs
        run_cands = ([ppr] if ppr is not None else []) + cands

        algn = para_attr(ppr, cands, 'algn', 'l')
        mar_l = float(para_attr(ppr, cands, 'marL', '0'))
        indent = float(para_attr(ppr, cands, 'indent', '0'))

        ln_spc = para_child(ppr, cands, 'a:lnSpc')
        line_height = LINE_BASE
        if ln_spc is not None:
            pct = ln_spc.find(q('a:spcPct'))
            pts = ln_spc.find(q('a:spcPts'))
            if pct is not None:
                line_height = int(pct.get('val')) / 100000 * LINE_BASE
            elif pts is not None:
                line_height = f'{fmt(int(pts.get("val")) / 100 * PT_TO_PX)}px'
        if isinstance(line_height, float):
            line_height = max(line_height * (1 - lnspc_red), 0.9)
            line_height = f'{line_height:.3f}'

        def spc_px(tag, font_px):
            el = para_child(ppr, cands, tag)
            if el is None:
                return 0.0
            pts = el.find(q('a:spcPts'))
            if pts is not None:
                return int(pts.get('val')) / 100 * PT_TO_PX
            pct = el.find(q('a:spcPct'))
            if pct is not None:
                return int(pct.get('val')) / 100000 * font_px
            return 0.0

        mar_l_px = emu2px(mar_l)
        ind_px = emu2px(indent)

        # runs
        runs = [ch for ch in p if etree.QName(ch).localname in ('r', 'br', 'fld')]
        end_rpr = p.find(q('a:endParaRPr'))

        # bullet
        kind, bchar, bfmt, bfont, bclr, bsz = bullet_props(ppr, cands)
        has_text = any(etree.QName(r).localname != 'br' and ''.join(t.text or '' for t in r.iter(q('a:t'))).strip() for r in runs)
        bullet_html = ''
        if kind != 'none' and has_text and lvl is not None:
            if kind == 'char':
                glyph = BULLET_CHAR_MAP.get((bfont, bchar), bchar)
            else:
                n = autonum_counters.get(lvl, 0) + 1
                autonum_counters[lvl] = n
                for k_ in list(autonum_counters):
                    if k_ > lvl:
                        del autonum_counters[k_]
                glyph = AUTONUM_FMT.get(bfmt, AUTONUM_FMT['arabicPeriod'])(n)
            # bullet occupies the hanging-indent gap (indent is negative)
            bstyle = (f'display:inline-block;width:{fmt(max(-ind_px, 0))}px;text-indent:0;'
                      if ind_px < 0 else '')
            if bclr is not None:
                bstyle += f'color:{css_color(*resolve_color(bclr, ctx))};'
            # bullet size relative to first run size
            first_sz = None
            for r in runs:
                if etree.QName(r).localname == 'r':
                    first_sz = run_prop(r.find(q('a:rPr')), run_cands, 'sz')
                    break
            if bsz and first_sz:
                bstyle += f'font-size:{fmt(float(first_sz) / 100 * PT_TO_PX * bsz * font_scale)}px;'
            bullet_html = f'<span class="bu" style="{bstyle}">{esc(glyph)}</span>'

        run_html = []
        max_sz_px = 0.0
        for r in runs:
            t = etree.QName(r).localname
            if t == 'br':
                run_html.append('<br>')
                continue
            if t == 'fld':
                continue  # slide numbers / dates — reveal handles its own
            rpr = r.find(q('a:rPr'))
            text = ''.join(tn.text or '' for tn in r.findall(q('a:t')))
            for pat, repl in TEXT_REPLACEMENTS:
                text = pat.sub(repl, text)
            if BANNED_RE.search(text):
                continue
            if text == '':
                continue
            sz = float(run_prop(rpr, run_cands, 'sz', '1800')) / 100 * font_scale
            max_sz_px = max(max_sz_px, sz * PT_TO_PX)
            bold = run_prop(rpr, run_cands, 'b', '0') == '1'
            ital = run_prop(rpr, run_cands, 'i', '0') == '1'
            under = run_prop(rpr, run_cands, 'u', 'none') != 'none'
            strike = run_prop(rpr, run_cands, 'strike', 'noStrike') != 'noStrike'
            base = run_prop(rpr, run_cands, 'baseline', None)
            spc = run_prop(rpr, run_cands, 'spc', None)
            # nearest style level wins, regardless of fill type
            fill = None
            levels = ([rpr] if rpr is not None else []) + \
                     [c.find(q('a:defRPr')) for c in run_cands]
            for lv in levels:
                if lv is None:
                    continue
                for tag_ in ('solidFill', 'pattFill', 'gradFill'):
                    el_ = lv.find(q('a:' + tag_))
                    if el_ is not None:
                        fill = el_
                        break
                if fill is not None:
                    break
            latin = run_child(rpr, run_cands, 'a:latin')
            font = resolve_font(latin.get('typeface') if latin is not None else None, ctx) or ctx.fonts['minor']
            color = None
            fancy_fill = ''
            if fill is not None and etree.QName(fill).localname == 'solidFill':
                color = css_color(*resolve_color(fill[0], ctx))
            elif fill is not None:
                grad = fill_css(fill, ctx)
                if grad:
                    fancy_fill = (f'background:{grad};-webkit-background-clip:text;'
                                  f'background-clip:text;color:transparent;')
            else:
                color = self._default_run_color
            outline = run_child(rpr, run_cands, 'a:ln')
            if outline is not None and outline.find(q('a:solidFill')) is not None:
                ow = emu2px(float(outline.get('w', '9525')))
                oc = css_color(*resolve_color(outline.find(q('a:solidFill'))[0], ctx))
                fancy_fill += f'-webkit-text-stroke:{fmt(max(ow, 0.5))}px {oc};'

            st = f'font-size:{fmt(sz * PT_TO_PX)}px;'
            st += f"font-family:'{font}',sans-serif;"
            if bold:
                st += 'font-weight:700;'
            if ital:
                st += 'font-style:italic;'
            deco = []
            if under:
                deco.append('underline')
            if strike:
                deco.append('line-through')
            if deco:
                st += f'text-decoration:{" ".join(deco)};'
            if color:
                st += f'color:{color};'
            st += fancy_fill
            if spc:
                st += f'letter-spacing:{fmt(float(spc) / 100 * PT_TO_PX)}px;'
            if base:
                pct = float(base) / 100000
                st += f'vertical-align:baseline;position:relative;top:{fmt(-pct * 0.6)}em;font-size:{fmt(sz * PT_TO_PX * 0.65)}px;'

            content = esc(text)
            hl = rpr.find(q('a:hlinkClick')) if rpr is not None else None
            if hl is not None and hl.get(q('r:id')):
                # external link target lives in the slide's rels; resolved later via data attr
                content = f'<a href="#" data-rid="{hl.get(q("r:id"))}">{content}</a>'
            run_html.append(f'<span style="{st}">{content}</span>')

        if not run_html:
            # empty paragraph keeps its line height
            sz = float((end_rpr.get('sz') if end_rpr is not None else None) or run_prop(None, run_cands, 'sz', '1800')) / 100 * font_scale
            max_sz_px = sz * PT_TO_PX
            run_html.append(f'<span style="font-size:{fmt(sz * PT_TO_PX)}px;">&nbsp;</span>')
            bullet_html = ''

        m_top = spc_px('a:spcBef', max_sz_px)
        m_bot = spc_px('a:spcAft', max_sz_px)

        # the <p> needs the paragraph's font size, otherwise the line-box strut
        # inherits Reveal's much larger base font size
        pstyle = (f'font-size:{fmt(max_sz_px)}px;'
                  f'text-align:{ {"l": "left", "ctr": "center", "r": "right", "just": "justify"}.get(algn, "left") };'
                  f'line-height:{line_height};margin:{fmt(m_top)}px 0 {fmt(m_bot)}px 0;')
        if mar_l_px or ind_px:
            pstyle += f'padding-left:{fmt(mar_l_px)}px;text-indent:{fmt(ind_px)}px;'
        return f'<p style="{pstyle}">{bullet_html}{"".join(run_html)}</p>'

    # -------- notes

    def notes_html(self, slide_part, ctx):
        notes_part = None
        for tgt, mode in self.pkg.rels(slide_part).values():
            if 'notesSlide' in tgt:
                notes_part = tgt
        if notes_part is None:
            return '<aside aria-label="speaker notes" class="notes"></aside>'
        notes = self.pkg.xml(notes_part)
        items = []
        for sp in notes.iter(q('p:sp')):
            ph = sp.find(q('p:nvSpPr') + '/' + q('p:nvPr') + '/' + q('p:ph'))
            if ph is None or ph.get('type') != 'body':
                continue
            for p in sp.iter(q('a:p')):
                ppr = p.find(q('a:pPr'))
                lvl = int(ppr.get('lvl', '0')) if ppr is not None else 0
                text = ''.join(t.text or '' for t in p.iter(q('a:t')))
                text = BANNED_RE.sub('', text).strip()
                if text:
                    items.append((lvl, text))
        if not items:
            return '<aside aria-label="speaker notes" class="notes"></aside>'
        out = ['<aside aria-label="speaker notes" class="notes">']
        depth = 0
        for lvl, text in items:
            while depth <= lvl:
                out.append('<ul>')
                depth += 1
            while depth > lvl + 1:
                out.append('</ul>')
                depth -= 1
            out.append(f'<li>{esc(text)}</li>')
        while depth > 0:
            out.append('</ul>')
            depth -= 1
        out.append('</aside>')
        return '\n'.join(out)

    # -------- hyperlink post-processing

    def resolve_links(self, html_str, slide_part):
        rels = self.pkg.rels(slide_part)

        def sub(m):
            rid = m.group(1)
            if rid in rels and rels[rid][1] == 'External':
                return f'href="{rels[rid][0]}" target="_blank"'
            return 'href="#"'

        return re.sub(r'href="#" data-rid="(rId\d+)"', sub, html_str)

    # -------- driver

    def run(self):
        # clean previous output so stale/renamed images never linger
        for f in os.listdir(self.img_dir):
            os.remove(os.path.join(self.img_dir, f))
        slides_dir = os.path.join(self.out_dir, 'slides')
        os.makedirs(slides_dir, exist_ok=True)
        # remove stale slide files
        for f in os.listdir(slides_dir):
            if f.endswith('.html'):
                os.remove(os.path.join(slides_dir, f))
        placeholders = []
        page = 0
        for slide_part in self.slide_parts:
            slide = self.pkg.xml(slide_part)
            if slide.get('show') == '0':
                continue
            if os.path.basename(slide_part) in DROPPED_SLIDES:
                continue
            page += 1
            sec_html = self.convert_slide(slide_part, page)
            sec_html = self.resolve_links(sec_html, slide_part)
            # extract inner content (between <section ...> and </section>)
            inner = re.sub(r'^<section[^>]*>\n?', '', sec_html)
            inner = re.sub(r'\n?</section>$', '', inner)
            pptx_name = os.path.basename(slide_part)
            slide_file = pptx_name.replace('.xml', '.html')
            with open(os.path.join(slides_dir, slide_file), 'w') as f:
                f.write(inner if inner.endswith('\n') else inner + '\n')
            placeholders.append(
                f'        <section data-pptx="{pptx_name}" data-page="{page}"'
                f' data-src="slides/{slide_file}"></section>'
            )
        html_out = HTML_TEMPLATE.replace('<!--SLIDES-->', '\n'.join(placeholders))
        with open(os.path.join(self.out_dir, 'index.html'), 'w') as f:
            f.write(html_out)
        css_dir = os.path.join(self.out_dir, 'css')
        os.makedirs(css_dir, exist_ok=True)
        with open(os.path.join(css_dir, 'custom.css'), 'w') as f:
            f.write(CUSTOM_CSS)
        # bitmaps fully replaced by inline SVGs are never referenced
        for fname in SVG_REPLACEMENTS:
            path = os.path.join(self.img_dir, fname)
            if os.path.exists(path):
                os.remove(path)
        for w in self.warnings:
            print('WARN:', w, file=sys.stderr)
        print(f'{page} slides written to {self.out_dir}/slides/ and index.html')


def _ph_type_match(a, b):
    grp = {
        'title': 'title', 'ctrTitle': 'title',
        'body': 'body', 'subTitle': 'body', 'obj': 'body', None: 'body',
        'pic': 'body', 'tbl': 'body',
    }
    return grp.get(a, a) == grp.get(b, b)


HTML_TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

    <title>arc42 &amp; LASR — Playful system insights for sustainable improvements</title>

    <link rel="stylesheet" href="fonts/fonts.css">
    <link rel="stylesheet" href="dist/reset.css">
    <link rel="stylesheet" href="dist/reveal.css">
    <link rel="stylesheet" href="dist/theme/white.css">
    <link rel="stylesheet" href="css/custom.css">
</head>
<body>
<div class="reveal">
    <div class="slides">

<!--SLIDES-->

    </div>
</div>

<script src="dist/reveal.js"></script>
<script src="dist/plugin/notes.js"></script>
<script src="dist/plugin/markdown.js"></script>
<script src="dist/plugin/search.js"></script>
<script src="dist/plugin/zoom.js"></script>
<script src="dist/plugin/highlight.js"></script>
<script>
// Load external slide HTML before Reveal initialises
(function() {
    var sections = document.querySelectorAll('section[data-src]');
    var pending = sections.length;
    function done() { if (--pending === 0) initReveal(); }
    sections.forEach(function(sec) {
        fetch(sec.getAttribute('data-src'))
            .then(function(r) { return r.text(); })
            .then(function(t) { sec.innerHTML = t; done(); })
            .catch(function() { done(); });
    });
    function initReveal() {
        Reveal.initialize({
            width: 960, height: 540, margin: 0, hash: true,
            slideNumber: "c/t", history: true, mouseWheel: true,
            transition: 'fade', navigationMode: "linear",
            plugins: [ RevealMarkdown, RevealHighlight, RevealNotes, RevealSearch, RevealZoom ]
        });
    }
})();
</script>
</body>
</html>
'''

CUSTOM_CSS = '''/* Generated by scripts/pptx2reveal.py — do not edit manually. */

.reveal .slides section {
    padding: 0;
    margin: 0;
    width: 960px;
    height: 540px;
}

.pcanvas {
    position: relative;
    width: 960px;
    height: 540px;
    overflow: hidden;
    font-family: 'Karla', sans-serif;
    color: #1B1B1B;
    text-align: left;
    /* webfont metrics run ~1-2% wider than PowerPoint's; tighten tracking so
       tightly fitted text boxes wrap exactly like the original */
    letter-spacing: -0.012em;
}

.pcanvas .tx p {
    margin: 0;
    word-wrap: break-word;
}

.pcanvas .bu {
    white-space: nowrap;
}

.pcanvas .tx a {
    color: inherit;
    text-decoration: underline;
}

.pcanvas img {
    max-width: none;
    max-height: none;
    margin: 0;
    border: 0;
    box-shadow: none;
}

.ptbl {
    border-collapse: collapse;
    table-layout: fixed;
    width: 100%;
    height: 100%;
    margin: 0;
    font-size: inherit;
}

.ptbl td {
    padding: 0;
}

/* fragments: simple fade-in like the PPTX entrance animation */
.reveal .pcanvas .fragment {
    transition: opacity .3s ease;
}
'''


def main():
    pptx = sys.argv[1] if len(sys.argv) > 1 else 'arc42AndLasr_talk - envite_original.pptx'
    out = sys.argv[2] if len(sys.argv) > 2 else 'docs'
    pdf = sys.argv[3] if len(sys.argv) > 3 else pptx.replace('.pptx', '_rendered.pdf')
    Converter(pptx, out, pdf).run()


if __name__ == '__main__':
    main()
