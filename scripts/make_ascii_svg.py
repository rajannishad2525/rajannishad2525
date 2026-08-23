#!/usr/bin/env python3
"""
assets/prepped.png -> ascii-portrait.svg

Har row apni <text> hai jise ek clip-rect left-to-right kholta hai, thodi der
ke antar se. Animation ek baar chalti hai aur ruk jati hai (forwards).

STATIC=1 -> bina animation ke, preview ke liye.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "prepped.png")
OUT = os.path.join(ROOT, "ascii-portrait.svg")
STATIC = os.environ.get("STATIC") == "1"

# 78 columns pe chehra ~45 chars chauda tha aur ek aankh ko 4 char milte the —
# feature banane ke liye kaafi nahi. 118 pe aankh/naak/hont sabko theek jagah
# milti hai. README mein ise chhota dikhate hain, to ghane chars barik detail
# ban jaate hain.
COLS = 118
RAMP = " .`:-=+*cs#%@"          # kam ink -> zyada ink
CHAR_W, LINE_H, FONT = 4.9, 8.7, 8.2
# Vignette ka falloff mid-tones banata hai. Ulti mapping mein wo mid-tone
# ghane chars ban ke chehre ke charon taraf halka sa halo de deta tha, isliye
# cut neeche rakha hai — jo bhi lagbhag safed hai wo background hai.
BG_CUT = 0.88
PAD = 14
BG = "#0d1117"

ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def main():
    im = Image.open(SRC).convert("L")
    w, h = im.size

    # Monospace glyph chaudai se lambai kam hoti hai (~1:2), isliye rows ko
    # aadha sample karo warna chehra kheench jaata hai.
    rows = max(1, int(h / w * COLS * CHAR_W / LINE_H))
    small = im.resize((COLS, rows), Image.LANCZOS)
    a = np.asarray(small, dtype=np.float32) / 255.0

    # Normalization sirf BEECH ke hisse pe — jahan chehra hota hai.
    #
    # Pehle poore non-white area pe percentile lagata tha, par usme baal (bahut
    # dark) aur shirt/background (bahut bright) dono aa jaate the. Nateeja: unka
    # spread poori range kha jaata tha aur chehra beech mein dab ke sparse chars
    # pe chala jaata tha — sar dikhta tha, chehra khaali.
    r0, r1 = int(rows * 0.22), int(rows * 0.86)
    c0, c1 = int(COLS * 0.20), int(COLS * 0.82)
    core = a[r0:r1, c0:c1]
    core = core[core < 0.97]
    if core.size:
        lo, hi = np.percentile(core, 6), np.percentile(core, 94)
        if hi > lo:
            a = np.clip((a - lo) / (hi - lo), 0, 1)

    # Mapping ULTI hai, aur jaan-boojh ke.
    #
    # Kaagaz pe ASCII art dark ink se banti hai, to gehra pixel = ghana glyph.
    # Par ye SVG dark terminal (#0d1117) pe hare akshar se render hoti hai —
    # yahan ghana glyph ka matlab ZYADA roshni hai. Kaagaz wali mapping lagane
    # se chamakti hui skin ko khaali chars milte the (chehra gayab) aur baal
    # sabse ghane (sirf sar dikhta tha). Bright -> dense se chehra jagmagata hai
    # aur baal peeche chale jaate hain, bilkul jaise asli roshni padti hai.
    n = len(RAMP) - 1
    lines = []
    for r in range(rows):
        row = "".join(
            " " if a[r, c] > BG_CUT else RAMP[int(round(a[r, c] * n))]
            for c in range(COLS)
        )
        lines.append(row.rstrip())

    # upar/neeche ki khaali rows hata do
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    W = int(PAD * 2 + COLS * CHAR_W)
    H = int(PAD * 2 + len(lines) * LINE_H)

    body, clips = [], []
    for i, line in enumerate(lines):
        y = PAD + (i + 1) * LINE_H - 3
        txt = "".join(ESC.get(ch, ch) for ch in line)
        if STATIC:
            body.append(f'<text x="{PAD}" y="{y:.1f}" xml:space="preserve">{txt}</text>')
            continue
        cid = f"w{i}"
        delay = 0.10 + i * 0.028
        clips.append(
            f'<clipPath id="{cid}"><rect x="{PAD}" y="{y - LINE_H:.1f}" '
            f'width="0" height="{LINE_H + 4:.1f}">'
            f'<animate attributeName="width" from="0" to="{COLS * CHAR_W}" '
            f'begin="{delay:.2f}s" dur="0.42s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0.7 0.3 1" keyTimes="0;1"/>'
            f'</rect></clipPath>')
        body.append(
            f'<text x="{PAD}" y="{y:.1f}" clip-path="url(#{cid})" xml:space="preserve">{txt}</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="ASCII portrait of Rajan Nishad">
<defs>
<linearGradient id="ink" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="#39d353"/>
  <stop offset="55%" stop-color="#7ee2a8"/>
  <stop offset="100%" stop-color="#58a6ff"/>
</linearGradient>
{chr(10).join(clips)}
</defs>
<style>
  text {{ font-family: ui-monospace, "SF Mono", "Cascadia Mono", Consolas, monospace;
          font-size: {FONT}px; fill: url(#ink); white-space: pre; }}
</style>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
{chr(10).join(body)}
</svg>
'''
    with open(OUT, "w", encoding="utf8") as f:
        f.write(svg)
    print(f"{OUT}  ({W}x{H}, {COLS}x{len(lines)} chars, {os.path.getsize(OUT)/1024:.1f} KB"
          f"{', static' if STATIC else ''})")

    print()
    for line in lines[::3]:
        print("   " + line)


if __name__ == "__main__":
    main()
