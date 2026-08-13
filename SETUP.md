# Setup

GitHub renders `README.md` from a repo whose name **matches your username**
as your profile page. So:

1. Create a new **public** repo named exactly `YOUR_USERNAME` (e.g. if your
   username is `jdoe`, the repo is `jdoe/jdoe`). GitHub will prompt you to
   do this the first time you visit your own profile if it doesn't exist yet.
2. Push everything in this folder to that repo's `main` branch.
3. Open `README.md` and replace every `YOUR_USERNAME`, the links, bio, stack,
   and project list with your own.
4. Run `python3 scripts/make_headings.py` locally (or edit the SVGs by hand)
   to change the section-heading titles/colors — this only needs to be
   re-run when you change wording, not automatically.
5. Go to the repo's **Actions** tab and manually run "refresh stats" once
   (`workflow_dispatch`) so `stats.svg`, `streak.svg`, `langs.svg`, and
   `year.svg` get generated for the first time. After that it runs itself
   daily at 05:17 UTC — no token setup needed, `GITHUB_TOKEN` is provided
   automatically by Actions.
6. Commit and you're done — the graphics will silently keep themselves
   up to date from then on.

## Notes / things you can tweak

- Colors, font stack, and card sizing all live at the top of
  `scripts/generate_stats.py` and `scripts/make_headings.py` — change the
  `BG` / `FG` / `ACCENT` constants for a different palette.
- `draw_year()` uses a quiet→loud character ramp (`" :+#@"`) over your last
  365 contribution days — one character per day.
- The workflow deliberately has no `push` trigger, since it commits the SVGs
  itself — that would otherwise loop.
- `ascii.svg` is already generated and sitting in this folder — see the
  ASCII PORTRAIT section below to regenerate it with your own photo.

## ASCII portrait (`ascii.svg`)

This is a one-off, not part of the daily Action — you only rerun it when
you want to swap the photo.

1. Have a clear, well-lit, front-facing-ish photo (the better the source
   lighting, the cleaner the result — very shadowed faces get muddy).
2. From the repo root:
   ```
   pip install pillow
   python3 scripts/make_ascii.py path/to/your-photo.jpg ascii.svg
   ```
3. Open `ascii.svg` in a browser to check it before committing — it renders
   like any other image file.
4. Commit `ascii.svg` alongside your other files and push.

## Typing animation (`typing.svg`)

Cycles through a list of lines with a real type/erase effect — pure SMIL
animation baked into the SVG itself, so it plays the moment your profile
loads, no JS and no third-party "typing-svg" service involved.

1. Open `scripts/make_typing.py` and edit the `LINES` list at the top to
   whatever you want it to say.
2. Regenerate: `python3 scripts/make_typing.py`
3. Commit `typing.svg` — it's already referenced in `README.md`.

Tunables in the same file: `TYPE_SPEED` / `ERASE_SPEED` (seconds per
character), `HOLD` (pause once a line is fully typed), `GAP` (pause once
erased before the next line starts), and `FG` / `FONT_SIZE` for styling.

Tunables at the top of `scripts/make_ascii.py`:
- `COLS` — characters per row (higher = more detail, bigger/slower file)
- `GAMMA` — >1 lifts shadow detail (raise this if your photo is dark/backlit)
- `MIN_LEVEL` — brightness floor so near-black pixels stay invisible against
  the dark card instead of turning into faint noise
- `SATURATION_BOOST` — how much color pop vs. the flat source photo
- `BG` — card background color, keep in sync with the other SVGs
