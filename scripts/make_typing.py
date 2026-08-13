#!/usr/bin/env python3
"""
Draws a self-hosted typewriter-effect SVG: cycles through a list of lines,
typing and erasing each one, using pure SMIL animation (no JS, no
third-party "readme-typing-svg" service -- just an image GitHub renders,
same philosophy as the other graphics in this repo).

Usage:
    python3 scripts/make_typing.py

Edit LINES below, then re-run.
"""

import os

# --- content ---------------------------------------------------------------
LINES = [
    "B.Tech CSE @ Manipal Institute of Technology",
    "Building with Next.js, FastAPI, Python",
    "Learning Azure, Docker & Kubernetes",
]
# ---------------------------------------------------------------------------

# --- style -------------------------------------------------------------------
WIDTH = 520
HEIGHT = 40
FG = "#58a6ff"
FONT = "'JetBrains Mono','Fira Code',Consolas,monospace"
FONT_SIZE = 20
CHAR_W = 12.1                 # approx monospace advance at this font-size
TYPE_SPEED = 0.09             # seconds per character while typing
ERASE_SPEED = 0.045           # seconds per character while erasing (faster)
HOLD = 1.2                    # seconds fully typed before erasing starts
GAP = 0.35                    # seconds fully erased before next line starts
# -------------------------------------------------------------------------

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "typing.svg")


def build_phases():
    """Returns list of dicts: start,t1(type end),t2(hold end),t3(erase end),full_w,line"""
    phases = []
    t = 0.0
    for line in LINES:
        n = len(line)
        type_dur = n * TYPE_SPEED
        erase_dur = n * ERASE_SPEED
        start = t
        t1 = start + type_dur
        t2 = t1 + HOLD
        t3 = t2 + erase_dur
        phases.append(dict(start=start, t1=t1, t2=t2, t3=t3, full_w=n * CHAR_W, line=line))
        t = t3 + GAP
    return phases, t  # t = CYCLE


def width_track(phases, cycle):
    """Single shared timeline for the clip-rect width / cursor x: 0-.-full-.-full-.-0 per phase."""
    pts = []
    for p in phases:
        pts += [(p["start"], 0.0), (p["t1"], p["full_w"]), (p["t2"], p["full_w"]), (p["t3"], 0.0)]
    pts.append((cycle, 0.0))
    clean = []
    for time_, val in pts:
        if clean and abs(clean[-1][0] - time_) < 1e-6:
            clean[-1] = (time_, val)
        else:
            clean.append((time_, val))
    key_times = ";".join(f"{t/cycle:.6f}" for t, _ in clean)
    values = ";".join(f"{v:.2f}" for _, v in clean)
    return key_times, values


def opacity_track(phase, cycle):
    """This line's text is visible only from its own start to its own erase-end."""
    pts = [(0.0, 0.0), (phase["start"], 0.0), (phase["start"], 1.0),
           (phase["t3"], 1.0), (phase["t3"], 0.0), (cycle, 0.0)]
    fixed = []
    eps = 1e-4
    for time_, val in pts:
        if fixed and time_ <= fixed[-1][0]:
            time_ = fixed[-1][0] + eps
        fixed.append((time_, val))
    if fixed[-1][0] < cycle:
        fixed.append((cycle, fixed[-1][1]))
    key_times = ";".join(f"{t/cycle:.6f}" for t, _ in fixed)
    values = ";".join(f"{v:.0f}" for _, v in fixed)
    return key_times, values


def main():
    phases, cycle = build_phases()
    w_keytimes, w_values = width_track(phases, cycle)

    texts = ""
    for p in phases:
        o_keytimes, o_values = opacity_track(p, cycle)
        escaped = p["line"].replace("&", "&amp;").replace("<", "&lt;")
        texts += (
            f'\n  <text x="0" y="{FONT_SIZE}" font-family="{FONT}" font-size="{FONT_SIZE}" '
            f'fill="{FG}" clip-path="url(#reveal)" opacity="0">'
            f'<animate attributeName="opacity" dur="{cycle:.3f}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{o_keytimes}" values="{o_values}"/>'
            f"{escaped}</text>"
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <clipPath id="reveal">
      <rect x="0" y="0" width="0" height="{FONT_SIZE + 12}">
        <animate attributeName="width" dur="{cycle:.3f}s" repeatCount="indefinite"
                 calcMode="linear" keyTimes="{w_keytimes}" values="{w_values}"/>
      </rect>
    </clipPath>
  </defs>
  <g transform="translate(4,{(HEIGHT-FONT_SIZE)/2 - 2})">{texts}
    <rect x="0" y="-2" width="10" height="{FONT_SIZE + 4}" fill="{FG}">
      <animate attributeName="x" dur="{cycle:.3f}s" repeatCount="indefinite"
               calcMode="linear" keyTimes="{w_keytimes}" values="{w_values}"/>
      <animate attributeName="opacity" values="1;1;0;0" dur="1s" repeatCount="indefinite"/>
    </rect>
  </g>
</svg>"""

    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} (cycle {cycle:.1f}s)")


if __name__ == "__main__":
    main()
