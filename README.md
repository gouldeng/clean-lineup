# Clean Lineup

A static site that answers "is the water clean, how cold is it, and what should I wear?" for 65 Southern California surf spots, from Santa Barbara to Imperial Beach.

## How it works

```
fetch.py  ──►  data/spots.json  ──►  build.py  ──►  site/   (plain HTML/CSS/JS)
```

- `spots.py` lists the spots: name, county, lat/lon, a short blurb, and which official monitoring stations each one maps to.
- `fetch.py` pulls every source, records which ones worked in `sources`, and writes `data/spots.json`.
- `build.py` renders the following into `site/`:
  - the home page
  - `/spots/<slug>/` pages
  - `/about/`
  - `sitemap.xml` and `robots.txt`
- `.github/workflows/update.yml` runs both scripts on every push to `main`, on manual dispatch and every 3 hours, commits the new data, and deploys `site/` to GitHub Pages at https://cleanlineup.com (custom domain; `build.py` writes `site/CNAME`).

## Sources

| Data | Source | Notes |
|---|---|---|
| SD status | County of San Diego DEHQ, sdbeachinfo.com | This is an OutSystems app. A headless browser loads the public page and reads the site-list JSON it fetches. |
| LA status | LA County DPH beach map (Google My Maps KML) and the DPH advisory page | The advisory page is HTTP-only, so it is parsed for county-wide rain advisories. The map KML has no colour legend, so per-station results stay "No recent data". |
| OC status | OC Health Care Agency, ocbeachinfo.com | Closures, warnings and advisories are matched by keyword. The site may show a bot challenge, which is not bypassed; in that case OC shows "No recent data". |
| Ventura status | Ventura County Environmental Health, `VCSafeBeaches` ArcGIS feature layer (services5.arcgis.com/umIjvohPcWJU5ij6) | The public layer behind the county's sampling-results map. The `TEST` field is mapped with the county legend; unknown values stay "No recent data". The fetch fails (so spots show "No recent data") if the layer hasn't been edited in 14 days. |
| SB status | Santa Barbara County Environmental Health, `Ocean_Water_Quality_Points_Public` ArcGIS feature layer (services.arcgis.com/KkJhFbLnXVqahKz2) | The public layer behind the county's map. `Beach_status` Open/Open */Warning/Rain/Closed is used with its `StatusDate`; statuses older than 14 days are dropped. |
| Bacteria grades | Heal the Bay Beach Report Card | Uses the API behind beachreportcard.org, which is undocumented. Ask for permission before any commercial use. |
| Water temp | NOAA NDBC realtime2 (buoys and NOS/CO-OPS stations) | Uses the nearest station within 80 km that reported a water temperature in the last 6 h. |
| Rain | NWS api.weather.gov observations at KLAX, KSNA, KSAN, KOXR and KSBA | Sums the hourly precipitation in routine METARs over 72 h. A banner shows above 0.1 in. |

**Rule:** if a source fails, the affected spots show **No recent data**. Statuses are never guessed. OC shows "Open" only when ocbeachinfo.com was actually read and listed nothing for that area.

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium     # or set CHROME_PATH=/path/to/chrome
python fetch.py                           # ~1 min; writes data/spots.json
SITE_URL=https://cleanlineup.com python build.py   # the URL path becomes the link base
cd site && python -m http.server 8000
```

## What to wear

| Water temp | What to wear |
|---|---|
| ≥72°F | Boardshorts or a top |
| 66–71°F | Springsuit or 2mm |
| 62–65°F | 3/2 |
| 58–61°F | 4/3 |
| <58°F | 4/3 or 5/4 plus booties |

## Newsletter

Signup forms (home page, every spot page) post to Buttondown's embed endpoint for the `cleanlineup` account and open the confirm page in a new tab. Archive: https://buttondown.com/cleanlineup

## TODO

- Hosting: GitHub Pages with custom domain cleanlineup.com (DNS at Porkbun).
- The `UA` string in `fetch.py` identifies the bot with the repo URL.
- Ask Heal the Bay about API use. Confirm whether ocbeachinfo.com allows automated reads, or ask OCHCA for a feed.
- Wetsuit affiliate box: add links once you are in a program. It is marked TODO and has no links.
- LA: the DPH map KML publishes no legend and is currently all white (results pending after the Oct 21–26 rain advisory). Confirm the colour legend with DPH, then fill `LA_COLOR_STATUS` in `fetch.py`. The DPH advisory page is HTTP-only and may not be reachable from every network.
- Rejected sources (checked Oct 2026): the data.ca.gov "Beach water quality postings and closures" dataset is about 7 months behind; State Water Board BeachWatch postings lag 1–2 weeks and leave stale open-ended postings, so neither is used for current status.
