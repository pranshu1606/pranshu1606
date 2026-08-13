#!/usr/bin/env python3
"""
Converts a photo into an ASCII-art SVG portrait for a GitHub profile README.

Usage:
    python3 scripts/make_ascii.py path/to/photo.jpg [output.svg]

Renders as monospace text on a dark card, colored per-cell from the source
image, so it reads as a portrait from a normal viewing distance but is
"drawn", not embedded pixels.
"""

import sys
from PIL import Image

# --- tunables -----------------------------------------------------------
COLS = 80                   # characters per row
CHAR_W = 6.6                # px per character cell, horizontal
CHAR_H = 11.5                # px per character cell, vertical (monospace ~1.6-1.7x width)
BG = "#0d1117"
RAMP = " .:-=+*#%@"        # dark -> light
FONT = "'JetBrains Mono','Fira Code',Consolas,monospace"
FONT_SIZE = 11
SATURATION_BOOST = 1.25     # >1 makes colors pop a bit more than the flat photo
GAMMA = 1.7                 # >1 lifts shadows so a shadowed face still shows detail
MIN_LEVEL = 0.10            # brightness floor: darkest visible pixels still get a faint char
# -------------------------------------------------------------------------


def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, v))


def boost_saturation(r, g, b, factor):
    avg = (r + g + b) / 3
    return (
        clamp(int(avg + (r - avg) * factor)),
        clamp(int(avg + (g - avg) * factor)),
        clamp(int(avg + (b - avg) * factor)),
    )


def main():
    if len(sys.argv) < 2:
        print("usage: make_ascii.py <image> [output.svg]", file=sys.stderr)
        sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "ascii.svg"

    img = Image.open(src).convert("RGB")

    # target grid size, respecting the source aspect ratio and cell aspect ratio
    rows = int(COLS * (img.height / img.width) * (CHAR_W / CHAR_H))
    small = img.resize((COLS, rows), Image.LANCZOS)
    px = small.load()

    width = COLS * CHAR_W
    height = rows * CHAR_H

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">',
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="{BG}"/>',
        f'<g font-family="{FONT}" font-size="{FONT_SIZE}" '
        f'style="white-space:pre" xml:space="preserve">',
    ]

    for y in range(rows):
        row_chars = []
        cur_color = None
        buf = ""
        cy = y * CHAR_H + FONT_SIZE
        for x in range(COLS):
            r, g, b = px[x, y]
            brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            brightness = brightness ** (1 / GAMMA)
            if brightness < MIN_LEVEL:
                brightness = 0
            idx = min(len(RAMP) - 1, int(brightness * (len(RAMP) - 1)))
            ch = RAMP[idx]
            if ch == " ":
                if buf:
                    cx = (x - len(buf)) * CHAR_W
                    parts.append(
                        f'<text x="{cx:.1f}" y="{cy:.1f}" fill="{cur_color}">{buf}</text>'
                    )
                    buf = ""
                    cur_color = None
                continue
            rr, gg, bb = boost_saturation(r, g, b, SATURATION_BOOST)
            color = f"#{rr:02x}{gg:02x}{bb:02x}"
            if color != cur_color:
                if buf:
                    cx = (x - len(buf)) * CHAR_W
                    parts.append(
                        f'<text x="{cx:.1f}" y="{cy:.1f}" fill="{cur_color}">{buf}</text>'
                    )
                buf = ""
                cur_color = color
            buf += ch.replace("&", "&amp;").replace("<", "&lt;")
        if buf:
            cx = (COLS - len(buf)) * CHAR_W
            parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" fill="{cur_color}">{buf}</text>')

    parts.append("</g></svg>")

    with open(out, "w") as f:
        f.write("".join(parts))
    print(f"wrote {out}  ({COLS}x{rows} chars, {width:.0f}x{height:.0f}px)")


if __name__ == "__main__":
    main()
