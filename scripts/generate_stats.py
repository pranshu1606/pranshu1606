#!/usr/bin/env python3
"""
Pulls contribution / repo data from the GitHub GraphQL API and draws it
as plain SVG (no third-party badge services, nothing that can rate-limit
or go dark). Run daily by .github/workflows/stats.yml.

Requires env vars:
    GITHUB_TOKEN  - a token with read access (Actions provides this for free)
    GH_LOGIN      - the github username to report on
"""

import os
import sys
import json
import urllib.request

API_URL = "https://api.github.com/graphql"
BG = "#0d1117"
FG = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#58a6ff"
FONT = "'JetBrains Mono', 'Fira Code', Consolas, monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: [OWNER], isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


def gh_graphql(token, login):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats-script",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def compute_streaks(days):
    """days: list of {date, contributionCount} in chronological order."""
    current = longest = running = 0
    for d in days:
        if d["contributionCount"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak = trailing run ending today (allow today being 0 so far)
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        else:
            if d is days[-1]:
                continue  # today might just not have data yet
            break
    return current, longest


def card(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="10" fill="{BG}" '
        f'stroke="#30363d" stroke-width="1"/>'
        f"{body}</svg>"
    )


def draw_stats(out_path, followers, repo_count, stars, contributions):
    stats = [
        ("followers", followers),
        ("public repos", repo_count),
        ("stars", stars),
        ("contributions (1y)", contributions),
    ]
    rows = ""
    for i, (label, value) in enumerate(stats):
        y = 30 + i * 26
        rows += (
            f'<text x="16" y="{y}" font-family="{FONT}" font-size="13" fill="{DIM}">{label}</text>'
            f'<text x="284" y="{y}" font-family="{FONT}" font-size="13" fill="{FG}" '
            f'text-anchor="end" font-weight="700">{value}</text>'
        )
    svg = card(300, 26 * len(stats) + 20, rows)
    with open(out_path, "w") as f:
        f.write(svg)


def draw_streak(out_path, current, longest, total):
    boxes = [("current streak", current), ("longest streak", longest), ("total", total)]
    box_w = 100
    body = ""
    for i, (label, value) in enumerate(boxes):
        x = i * box_w
        body += (
            f'<g transform="translate({x},0)">'
            f'<text x="{box_w/2}" y="34" font-family="{FONT}" font-size="24" '
            f'font-weight="700" fill="{ACCENT}" text-anchor="middle">{value}</text>'
            f'<text x="{box_w/2}" y="54" font-family="{FONT}" font-size="10" '
            f'fill="{DIM}" text-anchor="middle">{label}</text>'
            f"</g>"
        )
    svg = card(box_w * 3, 70, body)
    with open(out_path, "w") as f:
        f.write(svg)


def draw_langs(out_path, langs):
    """langs: list of (name, color, pct) sorted desc, top ~6"""
    rows = ""
    bar_max = 200
    for i, (name, color, pct) in enumerate(langs):
        y = 22 + i * 24
        bar_w = max(2, bar_max * pct / 100)
        rows += (
            f'<circle cx="16" cy="{y-5}" r="5" fill="{color or DIM}"/>'
            f'<text x="30" y="{y}" font-family="{FONT}" font-size="12" fill="{FG}">{name}</text>'
            f'<rect x="150" y="{y-11}" width="{bar_max}" height="8" rx="4" fill="#30363d"/>'
            f'<rect x="150" y="{y-11}" width="{bar_w:.1f}" height="8" rx="4" fill="{color or ACCENT}"/>'
            f'<text x="{150+bar_max+8}" y="{y}" font-family="{FONT}" font-size="11" '
            f'fill="{DIM}">{pct:.1f}%</text>'
        )
    svg = card(360, 24 * len(langs) + 14, rows)
    with open(out_path, "w") as f:
        f.write(svg)


def draw_year(out_path, days):
    """One character per day, quiet -> loud ramp, last 365 days."""
    ramp = " :+#@"
    counts = [d["contributionCount"] for d in days]
    max_c = max(counts) if counts else 0

    def char_for(c):
        if max_c == 0:
            return ramp[0]
        idx = min(len(ramp) - 1, int((c / max_c) * (len(ramp) - 1)) if c > 0 else 0)
        return ramp[idx if c > 0 else 0]

    line = "".join(char_for(c) for c in counts)
    svg = card(
        820,
        50,
        f'<text x="16" y="30" font-family="{FONT}" font-size="11" fill="{ACCENT}" '
        f'xml:space="preserve">{line}</text>',
    )
    with open(out_path, "w") as f:
        f.write(svg)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    login = os.environ.get("GH_LOGIN")
    if not token or not login:
        print("GITHUB_TOKEN and GH_LOGIN must be set", file=sys.stderr)
        sys.exit(1)

    data = gh_graphql(token, login)
    if "errors" in data:
        print(json.dumps(data["errors"]), file=sys.stderr)
        sys.exit(1)

    user = data["data"]["user"]
    followers = user["followers"]["totalCount"]
    repos = user["repositories"]["nodes"]
    repo_count = user["repositories"]["totalCount"]
    stars = sum(r["stargazerCount"] for r in repos)

    cc = user["contributionsCollection"]["contributionCalendar"]
    total_contrib = cc["totalContributions"]
    days = [d for w in cc["weeks"] for d in w["contributionDays"]]
    current, longest = compute_streaks(days)

    # aggregate language bytes across repos
    lang_bytes = {}
    lang_color = {}
    for r in repos:
        for edge in r["languages"]["edges"]:
            name = edge["node"]["name"]
            lang_bytes[name] = lang_bytes.get(name, 0) + edge["size"]
            lang_color[name] = edge["node"]["color"]
    total_bytes = sum(lang_bytes.values()) or 1
    top_langs = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:6]
    langs = [(n, lang_color.get(n), b / total_bytes * 100) for n, b in top_langs]

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    draw_stats(os.path.join(root, "stats.svg"), followers, repo_count, stars, total_contrib)
    draw_streak(os.path.join(root, "streak.svg"), current, longest, total_contrib)
    draw_langs(os.path.join(root, "langs.svg"), langs)
    draw_year(os.path.join(root, "year.svg"), days[-365:])

    print("done")


if __name__ == "__main__":
    main()
