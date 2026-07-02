#!/usr/bin/env python3
"""Build assets/svg/preview.html: style tile with all sample SVGs inlined.

The SVGs are inlined (not <img>-referenced) so the self-hosted DM Sans
webfont applies to SVG text, exactly as it will when the generator inlines
them into the slides. Fonts are embedded as data URIs so the preview is a
single self-contained file.
"""
import base64
import pathlib
import re

HERE = pathlib.Path(__file__).parent
FONTS = HERE / "../../docs/fonts"

SAMPLES = [
    ("gear-warning.svg", "Zahnrad + Warnung", "Folie 2 &middot; Gear dreht träge (36s)"),
    ("yawning-person.svg", "Gähnende Person", "Folie 2 &middot; atmet dezent (5s)"),
    ("hello-badge.svg", "Hello-Badge", "Folie 3 &middot; statisch"),
    ("questions-doodle.svg", "Fragezeichen-Doodle", "Folie 10 &middot; ? wippt (7s)"),
    ("tech-network-emblem.svg", "Doku/Technik-Emblem", "Folie 11 &middot; Zahnrad dreht (30s)"),
    ("target-dartboard.svg", "Zielscheibe", "Folie 14 &middot; Radar-Ripple (5s)"),
    ("gears-lock.svg", "Zahnräder + Schloss", "Folie 15 &middot; Zahnräder drehen gegenläufig"),
    ("circuit-network.svg", "Leiterbahn-Netz", "Folie 16 &middot; Zentrum pulsiert (6s)"),
    ("chess-knight.svg", "Schach-Springer", "Folie 17 &middot; Funken blinken versetzt"),
    ("arrows-outward.svg", "Pfeile nach außen", "Folie 19 &middot; atmet (6s)"),
    ("checklist-gear.svg", "Checkliste + Zahnrad", "Folie 20 &middot; Zahnrad dreht (32s)"),
    ("circuit-checks.svg", "Geprüftes Netz", "Folie 21 &middot; Zentrum pulsiert (6s)"),
    ("paper-whirl.svg", "Papierwirbel", "Folie 22 &middot; Wirbel dreht (40s)"),
    ("book-magnifier.svg", "Buch + Lupe", "Folie 23 &middot; Lupe driftet (8s)"),
    ("thats-it-folks-rings.svg", "That's-it-folks-Ringe", "Folien 24/50 &middot; Zoom-Puls (8s)"),
    ("thats-it-folks-rings-grey.svg", "Ringe, grau", "Folien 25/51 &middot; statisch"),
    ("feather.svg", "Feder", "Folie 26 &middot; schwingt (6s)"),
    ("gamepad.svg", "Gamepad", "Folien 26/34/37/45/46/47 &middot; Amber-Knopf pulsiert (4s)"),
    ("person-suit.svg", "Person im Anzug", "Folie 26 &middot; statisch"),
    ("running-person.svg", "Rennende Person", "Folie 26 &middot; Tempolinien wandern"),
    ("audience-people.svg", "Publikum", "Folien 27/28 &middot; statisch"),
    ("warning-electric.svg", "Warndreieck Blitz", "Folie 36 &middot; Blitz flackert dezent (5s)"),
    ("document-magnifier.svg", "Dokument + Lupe", "Folien 36/45 &middot; Lupe driftet (8s)"),
    ("analyze-improve-cycle.svg", "Kreislauf", "Folie 51 &middot; Punkt läuft um (9s)"),
    ("feedback-badge.svg", "Feedback-Badge", "Folie 52 &middot; statisch, Texte/QR als HTML-Overlays"),
]

SWATCHES = [
    ("#1B1B1B", "Kontur / Text"),
    ("#6CCBB2", "Mint (Hauptfüllung)"),
    ("#B2E4D7", "Blassmint (Sekundär)"),
    ("#FFFFFF", "Weiß (Flächen)"),
    ("#F4AD0E", "Amber (1 Akzent max.)"),
    ("#3390C3", "Blau (nur Ringe)"),
    ("#90C5E2", "Hellblau (nur Ringe)"),
]

def font_face(family, weight, fname):
    data = base64.b64encode((FONTS / fname).read_bytes()).decode()
    return (f"@font-face{{font-family:'{family}';font-style:normal;"
            f"font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")

def main():
    fonts_css = "\n".join([
        font_face("DM Sans", 400, "DMSans-400-latin.woff2"),
        font_face("DM Sans", 700, "DMSans-700-latin.woff2"),
        font_face("Karla", 400, "Karla-400-latin.woff2"),
    ])

    cards = []
    for fname, title, note in SAMPLES:
        svg = (HERE / fname).read_text()
        svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
        cards.append(f"""
    <div class="card">
      <div class="stage"><div class="big">{svg}</div><div class="small">{svg}</div></div>
      <h3>{title}</h3>
      <p>{note}</p>
    </div>""")

    swatches = "".join(
        f'<div class="sw"><span style="background:{c}"></span>{c}<br><small>{label}</small></div>'
        for c, label in SWATCHES)

    html = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Stilprobe: SVG-Bildsprache</title>
<style>
{fonts_css}
body {{ font-family: 'Karla', sans-serif; color: #1B1B1B; background: #F2F2F2;
       margin: 0; padding: 32px; }}
h1, h2, h3 {{ font-family: 'DM Sans', sans-serif; }}
h1 {{ margin-top: 0; }}
.rules {{ max-width: 880px; line-height: 1.5; }}
.palette {{ display: flex; flex-wrap: wrap; gap: 14px; margin: 18px 0 30px; }}
.sw {{ font-size: 13px; }}
.sw span {{ display: block; width: 84px; height: 44px; border-radius: 6px;
            border: 1px solid #ccc; margin-bottom: 4px; }}
.grid {{ display: flex; flex-wrap: wrap; gap: 22px; }}
.card {{ background: #fff; border-radius: 10px; padding: 20px;
         box-shadow: 0 1px 4px rgba(0,0,0,.12); width: 330px; }}
.stage {{ display: flex; align-items: flex-end; gap: 16px; }}
.big svg {{ width: 220px; height: auto; }}
.small svg {{ width: 84px; height: auto; }}
.card h3 {{ margin: 14px 0 4px; }}
.card p {{ margin: 0; font-size: 14px; color: #3F3F3F; }}
</style>
</head>
<body>
<h1>Stilprobe: einheitliche SVG-Bildsprache</h1>
<p class="rules"><strong>Regeln:</strong> Duotone-Linienstil &mdash; Kontur #1B1B1B
(~3,5/100, runde Enden und Ecken), Füllungen Mint/Blassmint/Weiß, Amber für genau
ein Aufmerksamkeits-Element pro Bild, Blau nur für die That's-it-folks-Ringe
(Looney-Tunes-Hommage). Keine Schatten, keine Verläufe. Dezente Endlos-Loops
(4&ndash;8s), höchstens 1&ndash;2 animierte Elemente pro Bild;
<code>prefers-reduced-motion</code> wird respektiert. Jedes Bild wird in klein
(rechts) und groß (links) gezeigt &mdash; beide Größen kommen so im Deck vor.</p>
<div class="palette">{swatches}</div>
<div class="grid">{"".join(cards)}</div>
</body>
</html>"""
    out = HERE / "preview.html"
    out.write_text(html)
    print(f"wrote {out} ({out.stat().st_size//1024} KB)")

if __name__ == "__main__":
    main()
