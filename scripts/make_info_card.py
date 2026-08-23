#!/usr/bin/env python3
"""
info-card.svg — neofetch jaisa panel.

Zyada tar lines niche CARD mein hardcoded hain (badalni ho to wahin badlo).
Repo/follower counts GitHub API se live aate hain taaki stale na hon.

STATIC=1 se animation band, sirf preview ke liye.
"""
import json, os, sys, html, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "info-card.svg")
USER = os.environ.get("GH_USER", "rajannishad2525")
STATIC = os.environ.get("STATIC") == "1"

BG, FG, DIM = "#0d1117", "#c9d1d9", "#7d8590"
KEY, ACCENT, GREEN = "#58a6ff", "#f778ba", "#39d353"

W, PAD = 520, 20
LH, TOP = 19, 46


def gh(path, default=None):
    try:
        req = urllib.request.Request(
            f"https://api.github.com/{path}",
            headers={"User-Agent": "profile-art", "Accept": "application/vnd.github+json"})
        tok = os.environ.get("GITHUB_TOKEN")
        if tok:
            req.add_header("Authorization", f"Bearer {tok}")
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception as e:
        print(f"  (github api skip: {e})", file=sys.stderr)
        return default


def main():
    user = gh(f"users/{USER}", {}) or {}
    repos = gh(f"users/{USER}/repos?per_page=100", []) or []

    langs = {}
    for r in repos:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    top_langs = ", ".join(k for k, _ in sorted(langs.items(), key=lambda x: -x[1])[:4]) or "JavaScript, Python"

    contrib = {}
    cpath = os.path.join(ROOT, "data", "contributions.json")
    if os.path.exists(cpath):
        contrib = json.load(open(cpath, encoding="utf8"))

    # ── yahan apni details badlo ──────────────────────────────────────────────
    CARD = [
        ("Role",     "B.Tech CSE @ GNIOT, Greater Noida"),
        ("Building", "ryzenstudy.com - free AKTU question papers"),
        ("Scale",    "1,447 papers - 31,321 questions indexed"),
        ("Stack",    "Next.js 15, React 19, Tailwind, Node, Python"),
        ("Also",     "Electron desktop apps, Telegram bots, SEO"),
        ("Learning", "DSA in Java, Generative AI and agents"),
        ("Langs",    top_langs),
        ("Uptime",   "shipping since Mar 2026"),
    ]

    # Raw GitHub counts jaan-boojh ke band hain. Rajan ka zyada tar kaam VPS pe
    # deploy hota hai, GitHub pe commit nahi hota — to "5 repos / 29 commits"
    # us kaam ko chhota dikhata hai jo card ki upar wali lines bata rahi hain.
    # GitHub pe zyada push karna shuru karo to SHOW_GH_STATS=1 kar dena.
    if os.environ.get("SHOW_GH_STATS") == "1":
        CARD.append(("Repos", f'{user.get("public_repos", "-")} public'))
        if contrib:
            CARD.append(("Commits", f'{contrib["total"]} in the last year'))
    # ─────────────────────────────────────────────────────────────────────────

    name = user.get("name") or "Rajan Nishad"
    handle = f"{USER}@github"
    H = TOP + len(CARD) * LH + 30

    e = html.escape
    lines = [
        f'<text x="{PAD}" y="24" class="hd">{e(handle)}</text>',
        f'<text x="{PAD}" y="38" class="rule">{"-" * 34}</text>',
    ]
    for i, (k, v) in enumerate(CARD):
        y = TOP + i * LH
        delay = "" if STATIC else f' style="animation-delay:{0.12 + i * 0.07:.2f}s"'
        lines.append(
            f'<g class="row"{delay}>'
            f'<text x="{PAD}" y="{y}" class="k">{e(k)}</text>'
            f'<text x="{PAD + 82}" y="{y}" class="v">{e(v)}</text>'
            f'</g>')

    dots_y = H - 14
    dots = "".join(
        f'<circle cx="{PAD + 6 + i * 15}" cy="{dots_y}" r="5" fill="{c}" opacity=".85"/>'
        for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f", KEY, ACCENT, GREEN]))

    anim = "" if STATIC else """
  .row { opacity:0; animation: slide .5s cubic-bezier(.2,.7,.3,1) forwards; }
  @keyframes slide { from { opacity:0; transform: translateX(-10px); }
                     to   { opacity:1; transform: translateX(0);     } }
  @media (prefers-reduced-motion: reduce) { .row { animation:none; opacity:1; } }"""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{e(name)} - profile card">
<style>
  text {{ font-family: ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace; }}
  .hd   {{ font-size:13px; font-weight:700; fill:{ACCENT}; }}
  .rule {{ font-size:13px; fill:{DIM}; }}
  .k    {{ font-size:12px; font-weight:700; fill:{KEY}; }}
  .v    {{ font-size:12px; fill:{FG}; }}{anim}
</style>
<rect width="{W}" height="{H}" rx="8" fill="{BG}" stroke="#30363d"/>
{chr(10).join(lines)}
{dots}
</svg>
'''
    with open(OUT, "w", encoding="utf8") as f:
        f.write(svg)
    print(f"{OUT}  ({W}x{H}, {len(CARD)} rows{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
