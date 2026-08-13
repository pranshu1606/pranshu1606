#!/usr/bin/env python3
"""
Generates the little section-heading SVGs used in README.md
(hd-about.svg, hd-stack.svg, hd-projects.svg, hd-stats.svg, ...).

These only need to be regenerated when you change the titles/colors,
so this is a one-off script you run locally -- NOT part of the daily
Actions workflow (that one only redraws the data graphics).

Usage:
    python3 scripts/make_headings.py
"""

import os

OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Edit these to taste. (title, filename)
HEADINGS = [
    ("about", "hd-about.svg"),
    ("stack", "hd-stack.svg"),
    ("projects", "hd-projects.svg"),
    ("stats", "hd-stats.svg"),
]

BG = "#0d1117"
FG = "#c9d1d9"
ACCENT = "#58a6ff"

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40" viewBox="0 0 200 40">
  <rect width="200" height="40" fill="{bg}"/>
  <text x="0" y="26" font-family="'JetBrains Mono', 'Fira Code', Consolas, monospace"
        font-size="20" font-weight="700" fill="{fg}">
    <tspan fill="{accent}">#</tspan> {title}
  </text>
</svg>"""


def main():
    for title, filename in HEADINGS:
        svg = TEMPLATE.format(bg=BG, fg=FG, accent=ACCENT, title=title)
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w") as f:
            f.write(svg)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
