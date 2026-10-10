"""
Photo -> animated ASCII portrait SVG for a GitHub profile README.

  python scripts/make_ascii_portrait.py photo.jpg assets/ascii-portrait.svg
  STATIC=1 python ...   # final frame only (for previews)

Pipeline: remove background (rembg) -> local contrast (CLAHE) -> composite on
white -> sample into a character grid -> map brightness to a density ramp ->
emit an SVG terminal window where each row is wiped in left-to-right with a
block cursor riding the edge, rows staggered top to bottom (SMIL, plays on
GitHub because the SVG is loaded through <img>).
"""
import os
import sys
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image

COLS = int(os.environ.get("COLS", "100"))  # characters per row
CELL_ASPECT = 0.5         # monospace cell is ~2x taller than wide
RAMP = " .:-=+*csx#%@"    # sparse -> dense (dense = brightest, we draw light-on-dark)
STATIC = os.environ.get("STATIC") == "1"
KEEP = float(os.environ.get("KEEP", "1"))      # fraction of the subject kept from the top (0.4 = head & torso)
FLOOR = float(os.environ.get("FLOOR", "0.10"))  # min glyph density inside the subject, keeps dark clothes visible
GAMMA = float(os.environ.get("GAMMA", "1.0"))   # <1 lifts shadows
EDGE = float(os.environ.get("EDGE", "0.35"))    # how much edge outlines are mixed in

# layout (px)
W = 370
PAD_X, TOP, PAD_B = 18, 40, 16
CHAR_W = (W - 2 * PAD_X) / COLS
LINE_H = CHAR_W * 2 * 0.92          # slightly tighter than the cell aspect
FONT = CHAR_W * 1.62


def prep(path):
    img = Image.open(path).convert("RGB")
    crop = os.environ.get("CROP")  # "x0,y0,x1,y1" in source pixels, applied first
    if crop:
        img = img.crop(tuple(int(v) for v in crop.split(",")))
    if os.environ.get("SCENE") == "1":  # keep the background: render the whole frame
        g = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY).astype(np.float32)
        lo, hi = np.percentile(g, [1, 99])
        g = np.clip((g - lo) / max(1, hi - lo) * 255, 0, 255).astype(np.uint8)
        g = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8)).apply(g)
        return g, np.ones(g.shape, np.float32)
    try:
        from rembg import new_session, remove
        rgba = remove(img, session=new_session("u2net_human_seg"))
    except Exception as e:  # still works without background removal
        print("rembg unavailable, skipping background removal:", e)
        rgba = img.convert("RGBA")
    rgba = np.array(rgba)
    alpha = rgba[:, :, 3:4] / 255.0

    # crop to the subject
    ys, xs = np.where(rgba[:, :, 3] > 20)
    if len(xs):
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        m = int(0.04 * max(y1 - y0, x1 - x0))
        y0, x0 = max(0, y0 - m), max(0, x0 - m)
        y1, x1 = min(rgba.shape[0], y1 + m), min(rgba.shape[1], x1 + m)
        y1 = min(y1, y0 + int((y1 - y0) * KEEP) + m)
        rgba, alpha = rgba[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    gray = cv2.cvtColor(rgba[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    # stretch tones using only the subject's pixels (dim photos otherwise collapse to one shade)
    inside = alpha[:, :, 0] > 0.5
    lo, hi = np.percentile(gray[inside], [2, 98]) if inside.any() else (0, 255)
    gray = np.clip((gray - lo) / max(1, hi - lo) * 255, 0, 255).astype(np.uint8)
    gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(6, 6)).apply(gray)
    # edge emphasis: outlines of face, glasses, beard, folds read much better in ASCII
    blur = cv2.GaussianBlur(gray, (0, 0), max(1, gray.shape[1] / 300))
    edges = cv2.magnitude(cv2.Sobel(blur, cv2.CV_32F, 1, 0), cv2.Sobel(blur, cv2.CV_32F, 0, 1))
    edges = np.clip(edges / (np.percentile(edges[inside], 97) + 1e-6), 0, 1) if inside.any() else edges * 0
    gray = np.clip(gray.astype(np.float32) * (1 - EDGE) + 255 * edges * EDGE, 0, 255).astype(np.uint8)
    gray = gray * alpha[:, :, 0]                  # subject on black (background is masked anyway)
    return gray.astype(np.uint8), alpha[:, :, 0]


def to_ascii(gray, alpha):
    h, w = gray.shape
    rows = max(1, round(COLS * (h / w) * CELL_ASPECT / 0.92))
    small = cv2.resize(gray, (COLS, rows), interpolation=cv2.INTER_AREA)
    a = cv2.resize(alpha, (COLS, rows), interpolation=cv2.INTER_AREA)
    lines = []
    for r in range(rows):
        row = ""
        for c in range(COLS):
            if a[r, c] < 0.15:
                row += " "
                continue
            v = (small[r, c] / 255.0) ** GAMMA             # bright skin/highlights -> dense glyphs
            v = v if os.environ.get("SCENE") == "1" else FLOOR + (1 - FLOOR) * v
            row += RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
        lines.append(row.rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def svg(lines):
    H = TOP + len(lines) * LINE_H + PAD_B
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}">',
           '<defs>',
           f'<linearGradient id="ink" gradientUnits="userSpaceOnUse" x1="0" y1="{TOP}" x2="0" y2="{H:.0f}">'
           '<stop offset="0" stop-color="#7cffcb"/><stop offset=".55" stop-color="#5ee7ff"/>'
           '<stop offset="1" stop-color="#b48cff"/></linearGradient>']
    for i in range(len(lines)):
        y = TOP + i * LINE_H
        width = "100%" if STATIC else "0"
        anim = "" if STATIC else (
            f'<animate attributeName="width" from="0" to="{W}" begin="{0.4 + i * 0.045:.3f}s" '
            f'dur="0.55s" fill="freeze"/>')
        out.append(f'<clipPath id="r{i}"><rect x="0" y="{y - LINE_H:.2f}" width="{width}" '
                   f'height="{LINE_H + 1:.2f}">{anim}</rect></clipPath>')
    out.append('</defs>')

    # terminal window
    out.append(f'<rect width="{W}" height="{H:.0f}" rx="12" fill="#0d1117" stroke="#30363d"/>')
    out.append(f'<path d="M12 0.5h{W - 24}a11.5 11.5 0 0 1 11.5 11.5v14H.5V12A11.5 11.5 0 0 1 12 .5z" fill="#161b22"/>')
    for k, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{18 + k * 16}" cy="13" r="5" fill="{col}"/>')
    out.append('<text x="50%" y="17.5" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
               'font-size="11" fill="#8b949e">~/sanskar.ascii</text>')

    out.append(f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Courier New\',monospace" '
               f'font-size="{FONT:.2f}" fill="url(#ink)" xml:space="preserve">')
    for i, line in enumerate(lines):
        if not line:
            continue
        y = TOP + i * LINE_H
        # browsers collapse whitespace in SVG text: position each row from its first glyph
        # and use no-break spaces inside, then textLength pins it to the grid in any font
        lead = len(line) - len(line.lstrip(" "))
        body = line.lstrip(" ")
        x0 = PAD_X + lead * CHAR_W
        out.append(f'<text x="{x0:.2f}" y="{y:.2f}" textLength="{len(body) * CHAR_W:.2f}" lengthAdjust="spacingAndGlyphs" '
                   f'clip-path="url(#r{i})">{escape(body).replace(" ", "&#160;")}</text>')
    out.append('</g>')

    if not STATIC:  # block cursor riding each row's wipe edge, then gone
        for i, line in enumerate(lines):
            if not line:
                continue
            y = TOP + i * LINE_H
            b = 0.4 + i * 0.045
            out.append(
                f'<rect x="0" y="{y - LINE_H * 0.82:.2f}" width="{CHAR_W:.2f}" height="{LINE_H * 0.95:.2f}" '
                f'fill="#7cffcb" opacity="0">'
                f'<set attributeName="opacity" to="0.9" begin="{b:.3f}s"/>'
                f'<animate attributeName="x" from="{PAD_X}" to="{W}" begin="{b:.3f}s" dur="0.55s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{b + 0.55:.3f}s"/></rect>')
        # final blinking prompt cursor under the portrait
        y = TOP + len(lines) * LINE_H - LINE_H * 0.2
        end = 0.4 + len(lines) * 0.045 + 0.6
        out.append(f'<rect x="{PAD_X}" y="{y - LINE_H * 0.8:.2f}" width="{CHAR_W:.2f}" height="{LINE_H * 0.9:.2f}" '
                   f'fill="#7cffcb" opacity="0"><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.01;.5;.51" '
                   f'dur="1.1s" begin="{end:.2f}s" repeatCount="indefinite"/></rect>')
    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    lines = to_ascii(*prep(src))
    open(dst, "w").write(svg(lines))
    print(f"wrote {dst}: {len(lines)} rows x {COLS} cols")
