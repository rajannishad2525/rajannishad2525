#!/usr/bin/env python3
"""
GitHub ke public contributions HTML se calendar data nikaalo -> data/contributions.json

Koi token nahi chahiye. GitHub ye page bina auth ke deta hai:
    https://github.com/users/<user>/contributions
"""
import json, os, re, sys
import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER", "rajannishad2525")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "contributions.json")
URL = f"https://github.com/users/{USER}/contributions"


def parse_count(td, text):
    """Count kabhi data-count mein hota hai, kabhi sirf tooltip text mein."""
    if td.has_attr("data-count"):
        try:
            return int(td["data-count"])
        except ValueError:
            pass
    m = re.match(r"\s*(No|\d+)\s+contribution", text or "", re.I)
    if m:
        return 0 if m.group(1).lower() == "no" else int(m.group(1))
    return 0


def main():
    r = requests.get(URL, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (profile-art bot)",
        "Accept": "text/html",
    })
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # tooltip text alag element mein hota hai, id se td se juda hota hai
    tips = {t.get("for"): t.get_text(" ", strip=True)
            for t in soup.select("tool-tip[for]")}

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        text = tips.get(td.get("id"), "") or td.get_text(" ", strip=True)
        days.append({
            "date": date,
            "level": int(td.get("data-level") or 0),
            "count": parse_count(td, text),
        })

    if not days:
        print("!! ek bhi din nahi mila — GitHub ne HTML badla hoga", file=sys.stderr)
        sys.exit(1)

    days.sort(key=lambda d: d["date"])
    total = sum(d["count"] for d in days)

    # sabse lamba streak (aaj tak)
    best = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        best = max(best, cur)

    # abhi chal raha streak — aaj ka din 0 ho to usse ignore karo, din abhi baaki hai
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif current or d is not days[-1]:
            break

    payload = {
        "user": USER,
        "days": days,
        "total": total,
        "longestStreak": best,
        "currentStreak": current,
        "from": days[0]["date"],
        "to": days[-1]["date"],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf8") as f:
        json.dump(payload, f, indent=1)

    print(f"{len(days)} days | {total} contributions | "
          f"streak now {current}, best {best} | -> {OUT}")


if __name__ == "__main__":
    main()
