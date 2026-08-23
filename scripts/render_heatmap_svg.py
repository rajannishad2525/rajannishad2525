#!/usr/bin/env python3
"""
data/contributions.json -> contrib-heatmap.svg (animated)

GitHub README se <script> aur inline CSS hat jaati hai, par <img> ke through
render hui SVG ke andar ka CSS/SMIL chalta hai. Isliye saara animation SVG ke
andar hi rakha hai.
"""
import json, os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "contrib-heatmap.svg")

CELL, GAP, R = 11, 3, 2
PAD_L, PAD_T = 30, 26
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, FG, DIM = "#0d1117", "#c9d1d9", "#7d8590"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main():
    d = json.load(open(SRC, encoding="utf8"))
    days = d["days"]

    # Pehla column hamesha Sunday se shuru — GitHub ka calendar aisa hi hai.
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    lead = (first.weekday() + 1) % 7          # Mon=0 -> Sun=0
    cells = [None] * lead + days

    weeks = (len(cells) + 6) // 7
    W = PAD_L + weeks * (CELL + GAP) + 12
    H = PAD_T + 7 * (CELL + GAP) + 34

    rects, month_labels, seen_months = [], [], set()

    for i, day in enumerate(cells):
        wk, wd = divmod(i, 7)
        x = PAD_L + wk * (CELL + GAP)
        y = PAD_T + wd * (CELL + GAP)

        if day is None:
            continue

        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        if wd == 0 and dt.day <= 7 and dt.month not in seen_months:
            seen_months.add(dt.month)
            month_labels.append(
                f'<text x="{x}" y="{PAD_T - 8}" class="lbl">{MONTHS[dt.month - 1]}</text>')

        lvl = min(day["level"], 4)
        if day["count"] >= 10:                # apna extra bright level
            lvl = 5
        # diagonal reveal: upar-baayen se neeche-daayen
        delay = (wk + wd) * 0.018
        n = day["count"]
        tip = "No contributions" if n == 0 else f'{n} contribution{"s" if n != 1 else ""}'
        rects.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{R}" '
            f'fill="{PALETTE[lvl]}" class="c" style="animation-delay:{delay:.3f}s">'
            f'<title>{tip} on {day["date"]}</title></rect>')

    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD_T + wd * (CELL + GAP) + CELL - 2
        month_labels.append(f'<text x="4" y="{y}" class="lbl">{name}</text>')

    total, cur, best = d["total"], d["currentStreak"], d["longestStreak"]
    foot_y = H - 12
    legend_x = W - 12 - 5 * (CELL + 2) - 74

    legend = [f'<text x="{legend_x - 6}" y="{foot_y}" class="lbl" text-anchor="end">Less</text>']
    for i, c in enumerate(PALETTE[:5]):
        legend.append(f'<rect x="{legend_x + i * (CELL + 2)}" y="{foot_y - 9}" '
                      f'width="{CELL}" height="{CELL}" rx="{R}" fill="{c}"/>')
    legend.append(f'<text x="{legend_x + 5 * (CELL + 2) + 6}" y="{foot_y}" class="lbl">More</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution graph">
<style>
  .c {{ opacity:0; animation: pop .45s ease-out forwards; }}
  @keyframes pop {{ from {{ opacity:0; transform: translateY(-4px) scale(.4); }}
                    to   {{ opacity:1; transform: translateY(0)    scale(1);  }} }}
  .lbl  {{ font: 9px ui-monospace, "SF Mono", Consolas, monospace; fill:{DIM}; }}
  .stat {{ font: bold 11px ui-monospace, "SF Mono", Consolas, monospace; fill:{FG}; }}
  .num  {{ fill:#39d353; }}
  rect.c {{ transform-box: fill-box; transform-origin: center; }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ animation: none; opacity:1; }} }}
</style>
<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>
{chr(10).join(month_labels)}
{chr(10).join(rects)}
<text x="{PAD_L}" y="{foot_y}" class="stat"><tspan class="num">{total}</tspan> contributions &#183; streak <tspan class="num">{cur}</tspan> &#183; best <tspan class="num">{best}</tspan></text>
{chr(10).join(legend)}
</svg>
'''
    with open(OUT, "w", encoding="utf8") as f:
        f.write(svg)
    print(f"{OUT}  ({W}x{H}, {len(rects)} cells, {os.path.getsize(OUT)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
