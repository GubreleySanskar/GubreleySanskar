"""
Builds the two hand-made SVGs for the profile:
  assets/banner.svg     -> name in ANSI-shadow block letters, drawn as shapes
                           (font-independent), assembling column by column,
                           then a light sweep that loops
  assets/info-card.svg  -> neofetch-style terminal card: command types itself,
                           then each line slides in, ends on a blinking cursor

  python scripts/make_profile_art.py          # STATIC=1 for a frozen frame
Edit NAME / CARD below and re-run.
"""
import os
import re
from xml.sax.saxutils import escape

import pyfiglet

STATIC = os.environ.get("STATIC") == "1"
ROOT = os.path.join(os.path.dirname(__file__), "..")
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

NAME = "SANSKAR"
USER = "sanskar"
HOST = "github"
CARD = [  # (key, value) — keep values under ~40 chars
    ("Name", "Sanskar Gubreley"),
    ("Role", "Software Engineer @ Salesforce"),
    ("Creator", "Tech, AI & career content"),
    ("Topics", "SWE · AI · DSA · Career growth"),
    ("Mission", "Help students become great devs"),
    ("Status", "Shipping code & content daily"),
    ("Contact", "gubreley789@gmail.com"),
]
PALETTE = ["#30363d", "#ff5f56", "#27c93f", "#ffbd2e", "#5ee7ff", "#b48cff", "#7cffcb", "#e6edf3"]


# ───────────────────────────── banner ─────────────────────────────
def banner():
    rows = [r.rstrip() for r in pyfiglet.figlet_format(NAME, font="ansi_shadow").split("\n") if r.strip()]
    cols = max(len(r) for r in rows)
    W, cw, ch = 860, 0, 0
    cw = (W - 80) / cols
    ch = cw * 1.9
    H = int(len(rows) * ch + 40)
    ox, oy = (W - cols * cw) / 2, 20

    blocks, lines = [], []
    seg = {  # box-drawing char -> which edges the line reaches (from cell centre)
        "═": "lr", "║": "ud", "╗": "ld", "╔": "rd", "╝": "lu", "╚": "ru",
    }
    for r, row in enumerate(rows):
        for c, chr_ in enumerate(row):
            x, y = ox + c * cw, oy + r * ch
            if chr_ == "█":
                blocks.append((c, x, y))
            elif chr_ in seg:
                cx, cy = x + cw / 2, y + ch / 2
                ends = {"l": (x, cy), "r": (x + cw, cy), "u": (cx, y), "d": (cx, y + ch)}
                for e in seg[chr_]:
                    ex, ey = ends[e]
                    lines.append((c, f"M{cx:.1f} {cy:.1f}L{ex:.1f} {ey:.1f}"))

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<defs>',
         f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{ox}" y1="0" x2="{W - ox}" y2="0">'
         '<stop offset="0" stop-color="#7cffcb"/><stop offset=".5" stop-color="#5ee7ff"/>'
         '<stop offset="1" stop-color="#b48cff"/></linearGradient>',
         '<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
         '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/>'
         '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
         '<clipPath id="letters">']
    for _, x, y in blocks:
        o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw + .4:.1f}" height="{ch + .4:.1f}"/>')
    o.append('</clipPath></defs>')

    # shadow strokes
    o.append('<g stroke="#3b4a6b" stroke-width="1.6" fill="none" stroke-linecap="square">')
    for c, d in lines:
        a = "" if STATIC else (f'<animate attributeName="opacity" from="0" to="1" begin="{0.15 + c * 0.025:.3f}s" '
                               f'dur=".3s" fill="freeze"/>')
        o.append(f'<path d="{d}" opacity="{1 if STATIC else 0}">{a}</path>')
    o.append('</g>')

    # solid blocks, dropping in column by column
    o.append('<g fill="url(#g)">')
    for c, x, y in blocks:
        if STATIC:
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw + .4:.1f}" height="{ch + .4:.1f}"/>')
        else:
            b = 0.1 + c * 0.025
            o.append(f'<rect x="{x:.1f}" y="{y - 14:.1f}" width="{cw + .4:.1f}" height="{ch + .4:.1f}" opacity="0">'
                     f'<animate attributeName="opacity" from="0" to="1" begin="{b:.3f}s" dur=".25s" fill="freeze"/>'
                     f'<animate attributeName="y" from="{y - 14:.1f}" to="{y:.1f}" begin="{b:.3f}s" dur=".35s" fill="freeze"/>'
                     f'</rect>')
    o.append('</g>')

    # looping light sweep across the letters
    if not STATIC:
        o.append(f'<g clip-path="url(#letters)"><rect x="-220" y="0" width="160" height="{H}" fill="url(#shine)" '
                 f'transform="skewX(-20)"><animate attributeName="x" values="-220;{W + 200};{W + 200}" '
                 f'keyTimes="0;.45;1" dur="5s" begin="2.2s" repeatCount="indefinite"/></rect></g>')
    o.append('</svg>')
    return "\n".join(o)


# ───────────────────────────── info card ─────────────────────────────
def info_card(height):
    W, H = 490, max(height, 360)
    PAD, FS = 22, 14
    LH = max(25, min(34, (H - 120) / 13))  # spread rows to fill the card height
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<defs><linearGradient id="t" x1="0" x2="1"><stop offset="0" stop-color="#7cffcb"/>'
         '<stop offset="1" stop-color="#b48cff"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117" stroke="#30363d"/>',
         f'<path d="M12 .5h{W - 24}a11.5 11.5 0 0 1 11.5 11.5v14H.5V12A11.5 11.5 0 0 1 12 .5z" fill="#161b22"/>']
    for k, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        o.append(f'<circle cx="{18 + k * 16}" cy="13" r="5" fill="{col}"/>')
    o.append(f'<text x="50%" y="17.5" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#8b949e">'
             f'{USER}@{HOST}: ~</text>')
    o.append(f'<g font-family="{MONO}" font-size="{FS}" xml:space="preserve">')

    y = 62
    prompt = f'<tspan fill="#7cffcb">{USER}@{HOST}</tspan><tspan fill="#8b949e">:</tspan>' \
             f'<tspan fill="#5ee7ff">~</tspan><tspan fill="#8b949e">$ </tspan>'
    plen = len(f"{USER}@{HOST}:~$ ")
    cw = FS * 0.602  # monospace advance
    cmd = "neofetch --profile"
    # prompt, then the command typing itself (clip wipe in steps = one char per step)
    o.append(f'<text x="{PAD}" y="{y}" textLength="{(plen - 1) * cw:.1f}" lengthAdjust="spacingAndGlyphs">{prompt}</text>')
    tx = PAD + plen * cw
    o.append(f'<clipPath id="typ"><rect x="{tx}" y="{y - FS}" height="{FS + 6}" width="{len(cmd) * cw if STATIC else 0}">'
             + ("" if STATIC else f'<animate attributeName="width" from="0" to="{len(cmd) * cw:.1f}" begin=".5s" '
                                  f'dur="{len(cmd) * 0.06:.2f}s" calcMode="discrete" '
                                  f'values="{";".join(f"{i * cw:.1f}" for i in range(len(cmd) + 1))}" fill="freeze"/>')
             + '</rect></clipPath>')
    o.append(f'<text x="{tx:.1f}" y="{y}" fill="#e6edf3" clip-path="url(#typ)">{cmd}</text>')
    t0 = 0.5 + len(cmd) * 0.06 + 0.35

    def line(content, i, y):
        if STATIC:
            return f'<g><text x="{PAD}" y="{y}">{content}</text></g>'
        b = t0 + i * 0.13
        return (f'<g opacity="0" transform="translate(-12 0)">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur=".35s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" from="-12 0" to="0 0" '
                f'begin="{b:.2f}s" dur=".35s" fill="freeze"/>'
                f'<text x="{PAD}" y="{y}">{content}</text></g>')

    y += LH + 8
    i = 0
    title = f"{USER}@salesforce"
    o.append(line(f'<tspan fill="url(#t)" font-weight="700">{title}</tspan>', i, y)); i += 1; y += LH * .8
    o.append(line(f'</text><rect x="{PAD}" y="{y - 6}" width="{30 * cw:.0f}" height="2" rx="1" fill="#30363d"/><text>', i, y)); i += 1; y += LH * .9
    kw = max(len(k) for k, _ in CARD) + 1
    for k, v in CARD:
        o.append(line(f'<tspan fill="#5ee7ff" font-weight="700">{escape(k)}</tspan>'
                      f'<tspan fill="#8b949e">:</tspan>'
                      f'<tspan x="{PAD + (kw + 1) * cw:.1f}" fill="#e6edf3">{escape(v)}</tspan>', i, y)); i += 1; y += LH

    # neofetch colour strip
    y += 6
    sw = 26
    strip = "".join(f'<rect x="{PAD + n * sw}" y="{y - 14}" width="{sw}" height="18" fill="{c}"/>'
                    for n, c in enumerate(PALETTE))
    if STATIC:
        o.append(strip)
    else:
        b = t0 + i * 0.13
        o.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur=".4s" '
                 f'fill="freeze"/>{strip}</g>')
    i += 1
    y += LH + 10

    # final prompt with blinking block cursor
    end = t0 + i * 0.13
    o.append(f'<g opacity="{1 if STATIC else 0}">'
             + ("" if STATIC else f'<set attributeName="opacity" to="1" begin="{end:.2f}s"/>')
             + f'<text x="{PAD}" y="{y}" textLength="{(plen - 1) * cw:.1f}" lengthAdjust="spacingAndGlyphs">{prompt}</text>'
             f'<rect x="{PAD + plen * cw:.1f}" y="{y - FS + 1}" width="{cw:.1f}" height="{FS + 2}" fill="#7cffcb">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" '
             f'repeatCount="indefinite"/></rect></g>')
    o.append('</g></svg>')
    return "\n".join(o)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    portrait = os.path.join(ROOT, "assets", "ascii-portrait.svg")
    h = 520
    if os.path.exists(portrait):
        m = re.search(r'height="(\d+)"', open(portrait).read())
        h = int(m.group(1)) if m else h
    open(os.path.join(ROOT, "assets", "banner.svg"), "w").write(banner())
    open(os.path.join(ROOT, "assets", "info-card.svg"), "w").write(info_card(h))
    print("wrote assets/banner.svg, assets/info-card.svg (card height", h, ")")
