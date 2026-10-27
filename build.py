#!/usr/bin/env python3
"""Render data/spots.json into a static site in ./site."""
from __future__ import annotations

import json, os, shutil
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE_URL = (os.environ.get("SITE_URL") or "https://cleanlineup.com").rstrip("/")
BASE = urlparse(SITE_URL).path.rstrip("/")  # e.g. "/clean-lineup" on GitHub Pages project sites
PT = ZoneInfo("America/Los_Angeles")
COUNTY_ORDER = ["Santa Barbara", "Ventura", "Los Angeles", "Orange", "San Diego"]
STATUS_LABEL = {"open": "Open", "advisory": "Advisory / posted", "closed": "Closed", "unknown": "No recent data"}


def parse_dt(s):
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def pt(s, fmt="%a %b %-d, %-I:%M %p PT"):
    d = parse_dt(s)
    if not d:
        return s or "—"  # already a human label (e.g. LA map "Monday October 26, 2026 8:00AM")
    return d.astimezone(PT).strftime(fmt)


def ptdate(s):
    d = parse_dt(s)
    if d and (d.hour, d.minute) == (0, 0):  # date-only value stored as midnight UTC
        return d.strftime("%b %-d, %Y")
    return pt(s, "%b %-d, %Y")


def ago(s, now):
    d = parse_dt(s)
    if not d:
        return ""
    h = (now - d).total_seconds() / 3600
    if h < 1:
        return f"{max(1, round(h * 60))} min ago"
    if h < 48:
        return f"{round(h)} h ago"
    return f"{round(h / 24)} days ago"


def main():
    data = json.loads((ROOT / "data" / "spots.json").read_text())
    now = parse_dt(data["generated"])
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html", "xml"]))
    env.filters.update(pt=pt, ptdate=ptdate, ago=lambda s: ago(s, now), status_label=STATUS_LABEL.get)
    spots = data["spots"]
    by_county = [(c, [s for s in spots if s["county"] == c]) for c in COUNTY_ORDER]
    by_county = [(c, ss) for c, ss in by_county if ss]
    rain = [(c, r) for c, r in data["county_notes"]["rain"].items() if r and r.get("rain_flag")]
    ctx = dict(data=data, spots=spots, by_county=by_county, rain=rain, site_url=SITE_URL, base=BASE,
               generated=data["generated"], STATUS_LABEL=STATUS_LABEL)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "static").mkdir(parents=True)
    for f in (ROOT / "static").iterdir():
        shutil.copy(f, OUT / "static" / f.name)
    (OUT / "data").mkdir()
    shutil.copy(ROOT / "data" / "spots.json", OUT / "data" / "spots.json")

    def write(path, tpl, **kw):
        p = OUT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(env.get_template(tpl).render(**ctx, **kw))

    write("index.html", "index.html", canonical=f"{SITE_URL}/")
    write("about/index.html", "about.html", canonical=f"{SITE_URL}/about/")
    write("404.html", "404.html", canonical=f"{SITE_URL}/404.html")
    for s in spots:
        near = sorted((x for x in spots if x["county"] == s["county"] and x["slug"] != s["slug"]),
                      key=lambda x: (x["lat"] - s["lat"]) ** 2 + (x["lon"] - s["lon"]) ** 2)[:4]
        write(f"spots/{s['slug']}/index.html", "spot.html", s=s, nearby=near,
              canonical=f"{SITE_URL}/spots/{s['slug']}/")
    urls = [f"{SITE_URL}/", f"{SITE_URL}/about/"] + [f"{SITE_URL}/spots/{s['slug']}/" for s in spots]
    lastmod = now.strftime("%Y-%m-%d")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{lastmod}</lastmod><changefreq>hourly</changefreq></url>\n" for u in urls)
        + "</urlset>\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    (OUT / ".nojekyll").write_text("")
    host = urlparse(SITE_URL).hostname or ""
    if host and not host.endswith("github.io"):
        (OUT / "CNAME").write_text(host + "\n")  # GitHub Pages custom domain
    print(f"built {len(urls)} pages into {OUT}")


if __name__ == "__main__":
    main()
