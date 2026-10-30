#!/usr/bin/env python3
"""Generate a "Weekend Lineup" newsletter issue (Buttondown-friendly Markdown) from data/spots.json.

Writes newsletter/issue-YYYY-MM-DD.md. The file starts with a small front-matter block holding the
subject line; everything after the closing '---' is the email body to paste into Buttondown.
This script only writes a file. It never sends anything and never calls the Buttondown API.

Usage: python newsletter.py [--date YYYY-MM-DD] [--per-county 2] [--stdout]
"""
from __future__ import annotations

import argparse, json, os, re
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
SITE_URL = (os.environ.get("SITE_URL") or "https://cleanlineup.com").rstrip("/")
SIGNUP_URL = "https://buttondown.com/cleanlineup"
PT = ZoneInfo("America/Los_Angeles")
COUNTY_ORDER = ["Santa Barbara", "Ventura", "Los Angeles", "Orange", "San Diego"]
COUNTY_SHORT = {"Los Angeles": "LA"}
GRADE_RANK = {g: i for i, g in enumerate(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"])}
FOOTER = "Data from public county water-quality sources. Not a safety guarantee; always check posted signs."


def parse_dt(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
    except (ValueError, AttributeError):
        return None


def weekend(d: date):
    """The Saturday/Sunday on or after d (a Thursday issue covers the coming weekend)."""
    sat = d + timedelta(days=(5 - d.weekday()) % 7)
    return sat, sat + timedelta(days=1)


def span(sat, sun, long=False):
    a = f"{sat:%a %b} {sat.day}" if long else f"{sat:%b} {sat.day}"
    b = (f"{sun:%a} " if long else "") + (f"{sun.day}" if sun.month == sat.month else f"{sun:%b} {sun.day}")
    return f"{a}–{b}"


def spot_url(s):
    return f"{SITE_URL}/spots/{s['slug']}/"


def temp(s):
    return f"{s['water_temp_f']:.0f}°F" if s.get("water_temp_f") is not None else "temp n/a"


def grade_key(s):
    g = (s.get("grade") or {}).get("dry")
    return GRADE_RANK.get(g, 99)


def pick_clean(spots, per_county):
    """Per county: spots whose official status is open, best latest dry-weather grade first."""
    out = []
    for c in COUNTY_ORDER:
        here = [s for s in spots if s["county"] == c]
        ok = [s for s in here if s["status"] == "open"]
        ok.sort(key=lambda s: (grade_key(s), s.get("water_temp_f") is None, s["name"]))
        if ok:
            out.append((c, ok[:per_county]))
        elif here and all(s["status"] == "unknown" for s in here):
            out.append((c, None))  # no official result posted for any spot in this county
    return out


def what_to_wear(spots, shop):
    keys = Counter(s.get("wear_key") for s in spots if s.get("wear_key"))
    if not keys:
        return None
    key, n = keys.most_common(1)[0]
    band = shop["bands"].get(key) or {}
    label = next(s["wear"] for s in spots if s.get("wear_key") == key)
    temps = [s["water_temp_f"] for s in spots if s.get("wear_key") == key and s.get("water_temp_f") is not None]
    rng = f"{min(temps):.0f}–{max(temps):.0f}°F" if temps else ""
    lead = f"**What to wear:** most spots ({n} of {sum(keys.values())}) are reading {rng}, so it's {label.lower()} weather."
    if band.get("picks"):
        p = shop["products"][band["picks"][0]]
        return f"{lead} Our pick: [{p['name']}]({p['url']}) (affiliate link), or browse [women's wetsuits]({shop['links']['womens']['url']}) (affiliate link)."
    return (f"{lead} If you run cold, browse Patagonia's [women's]({shop['links']['womens']['url']}) and "
            f"[men's]({shop['links']['mens']['url']}) wetsuits (affiliate links).")


def rain_note(data):
    rain = data.get("county_notes", {}).get("rain", {}) or {}
    flagged = [(c, r) for c, r in rain.items() if r and r.get("rain_flag")]
    wet = [(c, r) for c, r in rain.items() if r and not r.get("rain_flag") and (r.get("inches_72h") or 0) > 0]
    lines = []
    for c, r in flagged:
        left = f", about {r['hours_remaining']} h left in the 72-hour advisory window" if r.get("hours_remaining") else ""
        lines.append(f"{c}: {r['inches_72h']:.2f}\" at {r['station']} in the last 72 h{left}")
    for c, r in wet:
        lines.append(f"{c}: {r['inches_72h']:.2f}\" at {r['station']} (under the 0.1\" advisory threshold)")
    la = (data.get("county_notes", {}).get("la") or {}).get("page") or {}
    if la.get("rain_advisory"):
        lines.append("LA County Public Health has a rain advisory in effect")
    if not lines:
        return None
    return "**☔ Rain note:** " + "; ".join(lines) + ". Health officials advise staying out of the water for 72 hours after rain."


def build(data, shop, issue: date, per_county: int):
    spots = data["spots"]
    sat, sun = weekend(issue)
    gen = parse_dt(data["generated"]).astimezone(PT)
    clean = pick_clean(spots, per_county)
    skip = [s for s in spots if s["status"] in ("closed", "advisory")]
    n_open = sum(1 for s in spots if s["status"] == "open")
    temps = [s["water_temp_f"] for s in spots if s.get("water_temp_f") is not None]

    subject = f"Weekend Lineup {span(sat, sun)}: {n_open} spots open"
    if temps:
        subject += f", water {min(temps):.0f}–{max(temps):.0f}°F"

    md = [f"Hey crew, here's your weekend lineup for **{span(sat, sun, long=True)}**. "
          f"Of the {len(spots)} SoCal spots we track, {n_open} are officially open and {len(skip)} have an advisory or closure. "
          f"Statuses as of {gen:%a %-I:%M %p} PT, so check the live page before you paddle out.", ""]
    rn = rain_note(data)
    if rn:
        md += [rn, ""]
    md += ["## Cleanest spots this weekend", ""]
    for c, ss in clean:
        md.append(f"**{COUNTY_SHORT.get(c, c)}**")
        if ss is None:
            md += [f"- No official results posted for our {COUNTY_SHORT.get(c, c)} spots right now. Check [the live list]({SITE_URL}/).", ""]
            continue
        for s in ss:
            g = (s.get("grade") or {}).get("dry")
            gtxt = f" · grade {g}" if g and g != "ns" else ""
            md.append(f"- [{s['name']}]({spot_url(s)}): Open · {temp(s)} · {s.get('wear') or 'no temp data'}{gtxt}")
        md.append("")
    md += ["## Spots to skip", ""]
    if skip:
        for c in COUNTY_ORDER:
            ss = [s for s in skip if s["county"] == c]
            if ss:
                items = ", ".join(f"[{s['name']}]({spot_url(s)}) ({'closed' if s['status'] == 'closed' else 'advisory'})" for s in ss)
                md.append(f"- **{COUNTY_SHORT.get(c, c)}:** {items}")
    else:
        md.append("- No advisories or closures at our spots right now.")
    md.append("")
    w = what_to_wear(spots, shop)
    if w:
        md += [w, ""]
    # Weekend forecast intentionally omitted: fetch.py doesn't pull a forecast, and we don't make one up.
    md += [f"**Forward this to a buddy:** they can sign up at [buttondown.com/cleanlineup]({SIGNUP_URL}). "
           f"All spots live at [cleanlineup.com]({SITE_URL}/).", "", "---", "",
           f"*{FOOTER} Wetsuit links are affiliate links: {shop['disclosure']}*", ""]
    return subject, "\n".join(md)


def word_count(md):
    text = re.sub(r"\]\([^)]*\)", "]", md)
    return len(re.findall(r"[A-Za-z0-9°'+–-]+", text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="issue date YYYY-MM-DD (default: today in PT)")
    ap.add_argument("--per-county", type=int, default=2)
    ap.add_argument("--stdout", action="store_true")
    a = ap.parse_args()
    issue = date.fromisoformat(a.date) if a.date else datetime.now(PT).date()
    data = json.loads((ROOT / "data" / "spots.json").read_text())
    shop = json.loads((ROOT / "data" / "affiliate.json").read_text())
    subject, body = build(data, shop, issue, a.per_county)
    doc = f"---\nsubject: \"{subject}\"\n---\n\n{body}"
    if a.stdout:
        print(doc)
        return
    out = ROOT / "newsletter" / f"issue-{issue.isoformat()}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(doc)
    print(f"wrote {out} · subject: {subject} · ~{word_count(body)} words")


if __name__ == "__main__":
    main()
