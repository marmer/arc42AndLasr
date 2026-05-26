#!/usr/bin/env python3
"""
Extract vector shapes from a PPTX slide and write a clean SVG.

Primary strategy:  python-pptx for regular shapes (auto-shapes, text boxes,
                   connectors, grouped shapes).
Fallback strategy: raw ZIP + XML for SmartArt (ppt/diagrams/data*.xml).

Usage:
    python scripts/extract_svg.py \\
        --pptx  "arc42AndLasr_talk - envite_original.pptx" \\
        --slide 19 \\
        --output docs/img/slide-14-diagram.svg

Exit codes:
    0  SVG written; output path echoed to stdout
    1  No extractable diagram (image-only or empty slide); prints "no diagram needed"
    2  Error
"""
import sys
import argparse
import html as html_mod
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# ── SVG viewport (matches 16:9 widescreen) ───────────────────────────────────
SVG_W = 1200
SLIDE_W_EMU = 12192000
SLIDE_H_EMU = 6858000
SCALE = SVG_W / SLIDE_W_EMU
SVG_H = round(SLIDE_H_EMU * SCALE)   # 675

# ── Namespace shortcuts ───────────────────────────────────────────────────────
NS = {
    'a':   'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p':   'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r':   'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'dgm': 'http://schemas.openxmlformats.org/drawingml/2006/diagram',
}

SCHEME_COLORS = {
    'accent1': '#4472C4', 'accent2': '#ED7D31', 'accent3': '#A9D18E',
    'accent4': '#FFC000', 'accent5': '#5A96C8', 'accent6': '#70AD47',
    'dk1':  '#000000', 'dk2':  '#1F3864',
    'lt1':  '#FFFFFF', 'lt2':  '#E7E6E6',
    'tx1':  '#000000', 'tx2':  '#595959',
    'bg1':  '#FFFFFF', 'bg2':  '#E7E6E6',
}


# ── Unit helpers ─────────────────────────────────────────────────────────────
def emu(v) -> float:
    return round(int(v) * SCALE, 2)


def resolve_color(fill_elem) -> str | None:
    """Return '#RRGGBB' from a solidFill XML element, or None."""
    if fill_elem is None:
        return None
    srgb = fill_elem.find('a:srgbClr', NS)
    if srgb is not None:
        return f"#{srgb.get('val', '888888')[:6]}"
    scheme = fill_elem.find('a:schemeClr', NS)
    if scheme is not None:
        return SCHEME_COLORS.get(scheme.get('val', ''), '#888888')
    preset = fill_elem.find('a:prstClr', NS)
    if preset is not None:
        known = {'black': '#000000', 'white': '#FFFFFF', 'red': '#FF0000',
                 'green': '#008000', 'blue': '#0000FF', 'yellow': '#FFFF00'}
        return known.get(preset.get('val', ''), '#888888')
    return None


# ── Shape → SVG elements ─────────────────────────────────────────────────────
def xfrm_rect(xfrm_elem):
    """Return (x, y, w, h) in SVG units from an <a:xfrm> element."""
    off = xfrm_elem.find('a:off', NS)
    ext = xfrm_elem.find('a:ext', NS)
    if off is None or ext is None:
        return None
    return (emu(off.get('x', 0)), emu(off.get('y', 0)),
            emu(ext.get('cx', 0)), emu(ext.get('cy', 0)))


def shape_to_svg(sp_elem) -> list[str]:
    """Convert a <p:sp> element to a list of SVG element strings."""
    lines = []

    spPr = sp_elem.find('p:spPr', NS)
    if spPr is None:
        spPr = sp_elem.find('.//p:spPr', NS)
    if spPr is None:
        return lines

    xfrm = spPr.find('a:xfrm', NS)
    if xfrm is None:
        return lines
    rect = xfrm_rect(xfrm)
    if rect is None:
        return lines
    x, y, w, h = rect

    # Fill
    fill = 'none'
    sf = spPr.find('a:solidFill', NS)
    if sf is not None:
        c = resolve_color(sf)
        if c:
            fill = c
    noFill = spPr.find('a:noFill', NS)
    if noFill is not None:
        fill = 'none'

    # Stroke
    stroke = 'none'
    stroke_w = 1
    ln = spPr.find('a:ln', NS)
    if ln is not None:
        lsf = ln.find('a:solidFill', NS)
        if lsf is not None:
            c = resolve_color(lsf)
            if c:
                stroke = c
        w_attr = ln.get('w')
        if w_attr:
            stroke_w = max(1, round(emu(w_attr)))
        lnNoFill = ln.find('a:noFill', NS)
        if lnNoFill is not None:
            stroke = 'none'

    # Geometry
    prstGeom = spPr.find('a:prstGeom', NS)
    geom = prstGeom.get('prst', 'rect') if prstGeom is not None else 'rect'

    if geom == 'ellipse':
        cx, cy = round(x + w / 2, 2), round(y + h / 2, 2)
        lines.append(
            f'  <ellipse cx="{cx}" cy="{cy}" rx="{round(w/2,2)}" ry="{round(h/2,2)}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"/>'
        )
    elif geom in ('line', 'straightConnector1'):
        lines.append(
            f'  <line x1="{x}" y1="{y}" x2="{x+w}" y2="{y+h}" '
            f'stroke="{stroke or "#000"}" stroke-width="{stroke_w}"/>'
        )
    else:
        rx_attr = ' rx="8"' if geom == 'roundRect' else ''
        lines.append(
            f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"{rx_attr}/>'
        )

    # Text
    txBody = sp_elem.find('p:txBody', NS)
    if txBody is None:
        txBody = sp_elem.find('.//p:txBody', NS)
    if txBody is not None:
        text_parts = []
        for para in txBody.findall('a:p', NS):
            para_text = ''
            for r in para.findall('a:r', NS):
                t = r.find('a:t', NS)
                if t is not None and t.text:
                    para_text += t.text
            if para_text.strip():
                text_parts.append(para_text.strip())
        full_text = ' · '.join(text_parts)
        if full_text:
            cx = round(x + w / 2, 2)
            cy = round(y + h / 2, 2)
            safe = html_mod.escape(full_text)
            lines.append(
                f'  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="14" font-family="DM Sans, sans-serif" fill="#1B1B1B">{safe}</text>'
            )

    return lines


def collect_shapes(shape_elems) -> tuple[list, bool]:
    """
    Recursively collect (sp_elements, has_smartart) from a list of shape elements.
    Recurses into group shapes.
    """
    sp_elems = []
    has_smartart = False

    for elem in shape_elems:
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag == 'sp':
            sp_elems.append(elem)
        elif tag == 'grpSp':
            # Group: recurse into children
            children = list(elem)
            sub_sp, sub_sm = collect_shapes(children)
            sp_elems.extend(sub_sp)
            has_smartart = has_smartart or sub_sm
        elif tag == 'graphicFrame':
            gd = elem.find('.//a:graphicData', NS)
            if gd is not None and 'diagram' in gd.get('uri', '').lower():
                has_smartart = True
        elif tag == 'cxnSp':
            sp_elems.append(elem)   # connectors share <spPr> structure
        # pic → skip bitmaps

    return sp_elems, has_smartart


# ── SmartArt fallback ─────────────────────────────────────────────────────────
def extract_smartart_svg(pptx_path: Path, slide_idx: int) -> str | None:
    """
    Read SmartArt diagram data XML directly from the PPTX ZIP.
    Returns an SVG string or None if nothing useful found.
    """
    with zipfile.ZipFile(str(pptx_path), 'r') as zf:
        names = zf.namelist()

        # Slide rels: ppt/slides/_rels/slideN.xml.rels
        slide_num = slide_idx + 1
        rels_candidates = [
            f'ppt/slides/_rels/slide{slide_num}.xml.rels',
        ]
        diagram_data_file = None

        for rels_path in rels_candidates:
            if rels_path not in names:
                continue
            rels_xml = zf.read(rels_path)
            rels_root = ET.fromstring(rels_xml)
            for rel in rels_root:
                target = rel.get('Target', '')
                if 'diagrams/data' in target or 'diagram' in target.lower():
                    # Normalise path
                    if target.startswith('../'):
                        target = 'ppt/' + target[3:]
                    elif not target.startswith('ppt/'):
                        target = f'ppt/slides/{target}'
                    if target in names:
                        diagram_data_file = target
                        break

        # Fallback: grab any diagram data file referenced anywhere in the PPTX
        if diagram_data_file is None:
            candidates = [n for n in names if 'diagrams/data' in n and n.endswith('.xml')]
            if candidates:
                diagram_data_file = candidates[0]

        if diagram_data_file is None:
            return None

        dgm_xml = zf.read(diagram_data_file)

    root = ET.fromstring(dgm_xml)
    DGM = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'
    A   = 'http://schemas.openxmlformats.org/drawingml/2006/main'

    # Collect node texts
    node_texts = []
    for pt in root.findall(f'.//{{{DGM}}}pt'):
        pt_type = pt.get('type', 'node')
        if pt_type in ('parTrans', 'sibTrans'):
            continue
        text = ''
        for r_elem in pt.findall(f'.//{{{A}}}r'):
            t_elem = r_elem.find(f'{{{A}}}t')
            if t_elem is not None and t_elem.text:
                text += t_elem.text
        if text.strip():
            node_texts.append(text.strip())

    if not node_texts:
        return None

    # Render as a simple vertical list of labelled boxes
    box_h = 48
    gap = 16
    total_h = len(node_texts) * (box_h + gap) + gap
    box_w = SVG_W * 0.6
    box_x = (SVG_W - box_w) / 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_W} {total_h}" width="{SVG_W}" height="{total_h}">'
    ]
    for i, text in enumerate(node_texts):
        y = gap + i * (box_h + gap)
        safe = html_mod.escape(text)
        parts.append(
            f'  <rect x="{box_x:.1f}" y="{y}" width="{box_w:.1f}" height="{box_h}" '
            f'rx="8" fill="#6CCBB2"/>'
        )
        parts.append(
            f'  <text x="{SVG_W/2:.1f}" y="{y + box_h/2:.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-size="18" font-family="DM Sans, sans-serif" fill="white">{safe}</text>'
        )
    parts.append('</svg>')
    return '\n'.join(parts)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Extract SVG diagram from a PPTX slide')
    parser.add_argument('--pptx',   required=True, help='Path to the PPTX file')
    parser.add_argument('--slide',  type=int, required=True,
                        help='1-based PPTX slide number (not the presentation slide number)')
    parser.add_argument('--output', required=True, help='Output SVG path (e.g. docs/img/slide-14-diagram.svg)')
    args = parser.parse_args()

    try:
        from pptx import Presentation
    except ImportError:
        print('python-pptx not installed — run: pip install python-pptx', file=sys.stderr)
        sys.exit(2)

    pptx_path = Path(args.pptx)
    if not pptx_path.exists():
        print(f'PPTX not found: {pptx_path}', file=sys.stderr)
        sys.exit(2)

    prs = Presentation(str(pptx_path))
    all_slides = list(prs.slides)

    if args.slide < 1 or args.slide > len(all_slides):
        print(f'Slide {args.slide} out of range (1–{len(all_slides)})', file=sys.stderr)
        sys.exit(2)

    slide = all_slides[args.slide - 1]

    # Parse the slide XML directly for reliable shape detection
    slide_root = slide._element
    spTree = slide_root.find('.//p:spTree', NS)
    if spTree is None:
        print('no diagram needed')
        sys.exit(1)

    sp_elems, has_smartart = collect_shapes(list(spTree))

    if not sp_elems and not has_smartart:
        print('no diagram needed')
        sys.exit(1)

    svg_content = None

    # Primary: render regular shapes
    if sp_elems:
        all_lines = []
        for sp in sp_elems:
            all_lines.extend(shape_to_svg(sp))
        if all_lines:
            svg_content = (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="0 0 {SVG_W} {SVG_H}" width="{SVG_W}" height="{SVG_H}">\n'
                + '\n'.join(all_lines)
                + '\n</svg>'
            )

    # Fallback: SmartArt XML
    if svg_content is None and has_smartart:
        svg_content = extract_smartart_svg(pptx_path, args.slide - 1)

    if svg_content is None:
        print('no diagram needed')
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_content, encoding='utf-8')
    print(args.output)
    sys.exit(0)


if __name__ == '__main__':
    main()
