#!/usr/bin/env python3
"""Fetch official beach water-quality status, water temps and rainfall, and
normalize them into data/spots.json.

Rule: never invent a status. If a source fails or doesn't cover a spot, the spot
gets status "unknown" (rendered as "No recent data").
"""
from __future__ import annotations

import json, math, os, re, sys, time, traceback
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

import requests

from spots import SPOTS, LA_URL, OC_URL, SD_URL, VC_URL, SB_URL

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "spots.json"
UA = "CleanLineup/0.1 (+https://github.com/gouldeng/clean-lineup; static beach-status site)"
NOW = datetime.now(timezone.utc)
SEVERITY = {"closed": 3, "advisory": 2, "open": 1, "unknown": 0}

session = requests.Session()
session.headers["User-Agent"] = UA


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def km(a_lat, a_lon, b_lat, b_lon):
    p = math.pi / 180
    h = (math.sin((b_lat - a_lat) * p / 2) ** 2 + math.cos(a_lat * p) * math.cos(b_lat * p)
         * math.sin((b_lon - a_lon) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(h))


def slugify(s):
    s = s.lower().replace("'", "").replace("ñ", "n")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def text_of(html):
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


# ---------------------------------------------------------------- San Diego
def fetch_sd():
    """sdbeachinfo.com is an OutSystems app; its data comes from JSON
    'screenservices' calls whose URLs carry build hashes. Load the public page in
    headless Chrome and read those JSON responses, like a normal visitor."""
    from playwright.sync_api import sync_playwright
    caps = {}
    with sync_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        if os.environ.get("CHROME_PATH"):
            kw["executable_path"] = os.environ["CHROME_PATH"]
        b = p.chromium.launch(**kw)
        page = b.new_page(user_agent=UA + " HeadlessChrome")

        def on_resp(r):
            if "/screenservices/CoSD_Beach_Water_CW/" in r.url:
                try:
                    caps[r.url.rsplit("/", 1)[-1]] = r.json()
                except Exception:
                    pass
        page.on("response", on_resp)
        page.goto(SD_URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(3000)
        b.close()
    sites = caps["ScreenDataSetGetSiteById"]["data"]["List"]["List"]
    last = caps.get("DataActionGetLastDateTime", {}).get("data", {})
    last = next((v for v in last.values() if isinstance(v, str) and re.match(r"\d{4}-", v)), None)
    pr = {4: "closed", 3: "advisory", 2: "advisory", 1: "open"}  # 3 = warning/posted
    label = {4: "Closure", 3: "Warning (posted)", 2: "Advisory", 1: "Open"}
    out = {}
    for s in sites:
        p_ = int(s.get("PriorityMax") or 0)
        out[str(s["Id"])] = dict(status=pr.get(p_, "unknown"), label=label.get(p_, "Unknown"),
                                 name=f'{s["BeachName"]} – {s["LocationName"]}')
    counts = {k: sum(1 for v in out.values() if v["status"] == k) for k in SEVERITY}
    return dict(sites=out, updated=last, counts=counts)


# ---------------------------------------------------------------- Los Angeles
LA_KML = "https://www.google.com/maps/d/kml?mid=1hrin1gMc6ok2dKu9d1i9szZKC6Y&forcekml=1"
# The DPH map publishes no legend. Only colours whose meaning has been verified
# against the DPH page should be added here; anything else stays "unknown".
LA_COLOR_STATUS: dict[str, str] = {}


def fetch_la_map():
    r = session.get(LA_KML, timeout=30)
    r.raise_for_status()
    k = r.text
    folder = re.search(r"<Folder>\s*<name>(.*?)</name>", k, re.S)
    updated = folder.group(1).strip() if folder else None
    st = {}
    for pm in re.findall(r"<Placemark>(.*?)</Placemark>", k, re.S):
        name = re.sub(r"<!\[CDATA\[|\]\]>", "", re.search(r"<name>(.*?)</name>", pm, re.S).group(1)).strip()
        color = (re.search(r"icon-\d+-([0-9A-F]{6})", pm) or [None, None])[1]
        st[name] = dict(color=color, status=LA_COLOR_STATUS.get(color, "unknown"))
    return dict(stations=st, updated_label=updated, colors=sorted({v["color"] for v in st.values()}))


MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                      "august", "september", "october", "november", "december"], 1)}


def _la_dt(month, day, year, hhmm, ampm):
    h, m = (hhmm.split(":") + ["0"])[:2]
    h = int(h) % 12 + (12 if ampm.lower().startswith("p") else 0)
    from zoneinfo import ZoneInfo
    return datetime(int(year), MONTHS[month.lower()], int(day), h, int(m), tzinfo=ZoneInfo("America/Los_Angeles"))


def fetch_la_page():
    """County-wide rain advisory from the DPH ocean water page (plain HTTP only)."""
    r = session.get(LA_URL, timeout=25)
    r.raise_for_status()
    t = text_of(r.text)
    pat = r"(?:In Effect Until|ended|extended until|in effect until)\s+\w+day,\s+(\w+)\s+(\d+),\s+(\d{4}),?\s+at\s+(\d{1,2}(?::\d\d)?)\s*([ap])\.?m"
    until = None
    for m in re.finditer(r"In Effect Until\s+\w+day,\s+(\w+)\s+(\d+),\s+(\d{4}),?\s+at\s+(\d{1,2}(?::\d\d)?)\s*([ap])\.?m", t, re.I):
        d = _la_dt(*m.groups())
        until = max(until, d) if until else d
    ended = None
    for m in re.finditer(r"Advisory ended\s+\w+day,\s+(\w+)\s+(\d+),\s+(\d{4}),?\s+at\s+(\d{1,2}(?::\d\d)?)\s*([ap])\.?m", t, re.I):
        d = _la_dt(*m.groups())
        ended = max(ended, d) if ended else d
    active = bool(until and NOW < until and not (ended and ended >= until - timedelta(days=7) and ended <= NOW))
    return dict(rain_advisory=active, advisory_until=iso(until), advisory_ended=iso(ended))


# ---------------------------------------------------------------- Orange
def fetch_oc():
    r = session.get(OC_URL, timeout=30)
    if r.status_code == 202 or "sgcaptcha" in r.text:
        raise RuntimeError("ocbeachinfo.com returned a bot-protection challenge (not bypassed)")
    r.raise_for_status()
    t = text_of(r.text)
    def section(start, end):
        i = t.find(start)
        j = t.find(end, i + 1) if i >= 0 else -1
        if i < 0:
            raise RuntimeError(f"OC page layout changed: no '{start}'")
        s = t[i + len(start): j if j > 0 else i + 3000]
        if re.search(r"No ocean, harbor, or bay water [\w ]+ (?:is|are) currently in effect", s, re.I):
            return ""
        s = re.sub(r"^.*?(?:Click (?:a|an) [a-z]+ when displayed to see the (?:outlet )?location[^.]*\.)", "", s, flags=re.I)
        return s.strip()
    sec = dict(closed=section("CLOSURES", "WARNINGS"), advisory_w=section("WARNINGS", "ADVISORIES"),
               advisory=section("ADVISORIES", "The Environmental Health staff"))
    return dict(closures=sec["closed"], warnings=sec["advisory_w"], advisories=sec["advisory"])


# ---------------------------------------------------------------- Ventura / Santa Barbara (county ArcGIS layers)
# Both counties publish their beach map from a public ArcGIS Online feature layer;
# these are the same layers their official maps read. Read-only REST queries.
VC_LAYER = ("https://services5.arcgis.com/umIjvohPcWJU5ij6/arcgis/rest/services/"
            "VCSafeBeaches/FeatureServer/0")
SB_LAYER = ("https://services.arcgis.com/KkJhFbLnXVqahKz2/arcgis/rest/services/"
            "Ocean_Water_Quality_Points_Public/FeatureServer/0")


def _arcgis(layer):
    meta = session.get(layer, params={"f": "json"}, timeout=30)
    meta.raise_for_status()
    m = meta.json()
    if "error" in m:
        raise RuntimeError(f"ArcGIS error: {m['error']}")
    r = session.get(layer + "/query", params={"where": "1=1", "outFields": "*", "returnGeometry": "false",
                                              "f": "json"}, timeout=30)
    r.raise_for_status()
    q = r.json()
    if "error" in q or not q.get("features"):
        raise RuntimeError(f"ArcGIS query returned no features: {q.get('error')}")
    edited = (m.get("editingInfo") or {}).get("dataLastEditDate")
    edited = datetime.fromtimestamp(edited / 1000, timezone.utc) if edited else None
    return [f["attributes"] for f in q["features"]], edited


# Ventura's map legend (rma.venturacounty.gov sample-results page). Only these
# exact categories are mapped; any other value stays "unknown".
VC_TEST = [("meets state standards", "open"), ("warning", "advisory"),
           ("exceed", "advisory"), ("post-rainfall advisory", "advisory"),
           ("rainfall advisory", "advisory"), ("not sampled", "unknown")]


def fetch_vc():
    rows, edited = _arcgis(VC_LAYER)
    if edited and NOW - edited > timedelta(days=14):
        raise RuntimeError(f"Ventura layer not edited since {iso(edited)}; treating as stale")
    out = {}
    for a in rows:
        test = (a.get("TEST") or "").strip()
        status = next((s for k, s in VC_TEST if test.lower().startswith(k)), "unknown")
        sample = a.get("DATE") or "?"
        out[str(a["STATION_ID"])] = dict(status=status, name=f'{a["BEACH_NAME"]} (station {a["STATION_ID"]})',
                                         label=f'{test or "no status"} – sample {sample}, Enterococcus {a.get("ENTEROLERT")}')
    return dict(sites=out, updated=iso(edited))


SB_STATUS = {"open": "open", "open *": "open", "warning": "advisory", "rain": "advisory", "closed": "closed"}


def fetch_sb():
    rows, edited = _arcgis(SB_LAYER)
    out = {}
    for a in rows:
        raw = (a.get("Beach_status") or "").strip()
        sd = a.get("StatusDate")
        sd = datetime.fromtimestamp(sd / 1000, timezone.utc).strftime("%Y-%m-%d") if sd else None
        status = SB_STATUS.get(raw.lower(), "unknown")
        # a status older than 14 days is not "recent"
        if sd and NOW - datetime.fromisoformat(sd).replace(tzinfo=timezone.utc) > timedelta(days=14):
            status = "unknown"
        note = f' ({a["Notes"]})' if a.get("Notes") else ""
        out[a["Identifier"]] = dict(status=status, name=a["Beach_Name"],
                                    label=f'{raw or "no status"} as of {sd}{note} – Enterococcus {a.get("entercoccus_result")}')
    return dict(sites=out, updated=iso(edited))


# ---------------------------------------------------------------- Heal the Bay grades
def fetch_htb():
    r = session.get("https://admin.beachreportcard.org/api/locations", timeout=60)
    r.raise_for_status()
    out = {}
    for x in r.json():
        s = x.get("_source", x)
        try:
            lat, lon = float(s["geo"][0]), float(s["geo"][1])
        except Exception:
            continue
        out[int(s["id"])] = dict(id=int(s["id"]), title=s.get("title"), active=s.get("active"),
                                 county=s.get("county", ""), lat=lat, lon=lon, type=s.get("type"),
                                 dry_grade=s.get("dry_grade"), wet_grade=s.get("wet_grade"),
                                 grade_updated=s.get("grade_updated"))
    return out


# ---------------------------------------------------------------- Water temperature (NDBC)
def fetch_ndbc_stations():
    r = session.get("https://www.ndbc.noaa.gov/activestations.xml", timeout=30)
    r.raise_for_status()
    st = []
    for m in re.finditer(r"<station ([^>]*)>", r.text):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        try:
            lat, lon = float(a["lat"]), float(a["lon"])
        except Exception:
            continue
        if 32.3 < lat < 34.7 and -120.7 < lon < -117.0 and a.get("met") == "y":
            st.append(dict(id=a["id"], name=unescape(a.get("name", "")), lat=lat, lon=lon))
    return st


def ndbc_wtmp(sid):
    r = session.get(f"https://www.ndbc.noaa.gov/data/realtime2/{sid.upper()}.txt", timeout=20)
    if r.status_code != 200:
        return None
    lines = r.text.splitlines()
    hdr = lines[0].lstrip("#").split()
    if "WTMP" not in hdr:
        return None
    i = hdr.index("WTMP")
    for ln in lines[2:60]:
        c = ln.split()
        if len(c) > i and c[i] != "MM":
            t = datetime(int(c[0]), int(c[1]), int(c[2]), int(c[3]), int(c[4]), tzinfo=timezone.utc)
            return dict(c=float(c[i]), time=t)
    return None


def fetch_temps():
    res = {}
    for s in fetch_ndbc_stations():
        try:
            w = ndbc_wtmp(s["id"])
        except Exception:
            w = None
        if w and NOW - w["time"] < timedelta(hours=6) and 5 < w["c"] < 32:
            res[s["id"]] = dict(s, c=w["c"], f=round(w["c"] * 9 / 5 + 32, 1), time=iso(w["time"]))
        time.sleep(0.2)
    return res


# ---------------------------------------------------------------- Rain (NWS)
RAIN_STATIONS = {"Los Angeles": "KLAX", "Orange": "KSNA", "San Diego": "KSAN",
                 "Ventura": "KOXR", "Santa Barbara": "KSBA"}


def fetch_rain(station):
    start = NOW - timedelta(hours=72)
    url = f"https://api.weather.gov/stations/{station}/observations?start={iso(start)}&limit=500"
    feats = []
    for _ in range(5):
        r = session.get(url, timeout=30, headers={"Accept": "application/geo+json"})
        r.raise_for_status()
        d = r.json()
        f = d.get("features", [])
        feats += f
        if not f or len(f) < 500:
            break
        oldest = min(x["properties"]["timestamp"] for x in f)
        if oldest <= iso(start):
            break
        url = d.get("pagination", {}).get("next")
        if not url:
            break
    # Keep observations inside the window that carry a raw METAR. The hourly
    # precip group in special (SPECI) reports repeats the running total since the
    # last routine report, so only sum reports at the station's routine minute.
    obs = {}
    for x in feats:
        p = x["properties"]
        t = datetime.fromisoformat(p["timestamp"])
        if t >= start and p.get("rawMessage"):
            obs[t] = (p.get("precipitationLastHour") or {}).get("value")
    if not obs:
        raise RuntimeError(f"no METAR observations for {station}")
    minutes = [t.minute for t in obs]
    routine = max(set(minutes), key=minutes.count)
    total_mm, last = 0.0, None
    for t, v in obs.items():
        if t.minute == routine and v:
            total_mm += v
            last = max(last, t) if last else t
    seen = [t for t in obs if t.minute == routine]
    oldest = iso(min(obs))
    inches = round(total_mm / 25.4, 2)
    flag = inches > 0.1
    hours_left = None
    if flag and last:
        hours_left = max(0, round(72 - (NOW - last).total_seconds() / 3600))
    return dict(station=station, inches_72h=inches, last_rain=iso(last), rain_flag=flag,
                hours_remaining=hours_left, coverage_from=oldest, observations=len(seen))


# ---------------------------------------------------------------- helpers
def wear(f):
    """Return (label, wear_key) for a water temp in °F, or (None, None) with no reading.
    wear_key matches the bands in data/affiliate.json."""
    if f is None:
        return None, None
    if f >= 72:
        return "Boardshorts or a bikini/top", "boardshorts"
    if f >= 66:
        return "Springsuit or 2mm", "spring_2mm"
    if f >= 62:
        return "3/2 fullsuit", "full_3_2"
    if f >= 58:
        return "4/3 fullsuit", "full_4_3"
    return "4/3 or 5/4 plus booties", "cold_5_4"


def worst(statuses):
    known = [s for s in statuses if s != "unknown"]
    return max(known, key=SEVERITY.get) if known else "unknown"


def run(name, fn, sources, *a):
    t0 = time.time()
    try:
        v = fn(*a)
        sources[name] = dict(ok=True, seconds=round(time.time() - t0, 1))
        return v
    except Exception as e:
        sources[name] = dict(ok=False, error=f"{type(e).__name__}: {e}"[:300], seconds=round(time.time() - t0, 1))
        print(f"[warn] {name} failed: {e}", file=sys.stderr)
        if os.environ.get("DEBUG"):
            traceback.print_exc()
        return None


def main():
    sources = {}
    sd = run("sd_sdbeachinfo", fetch_sd, sources)
    la_map = run("la_dph_map_kml", fetch_la_map, sources)
    la_page = run("la_dph_page", fetch_la_page, sources)
    oc = run("oc_ocbeachinfo", fetch_oc, sources)
    vc = run("vc_safebeaches_arcgis", fetch_vc, sources)
    sb = run("sb_ocean_water_arcgis", fetch_sb, sources)
    htb = run("healthebay_grades", fetch_htb, sources) or {}
    temps = run("ndbc_water_temp", fetch_temps, sources) or {}
    rain = {}
    for county, st in RAIN_STATIONS.items():
        rain[county] = run(f"nws_rain_{st}", fetch_rain, sources, st)

    out = []
    for sp in SPOTS:
        c = sp["county"]
        rec = dict(name=sp["name"], slug=slugify(sp["name"]), county=c, lat=sp["lat"], lon=sp["lon"],
                   blurb=sp["blurb"], status="unknown", status_detail=None, stations=[],
                   source=None, source_url=None, status_updated=None)
        # ---- official status
        if c == "San Diego" and sp.get("sd_sites"):
            rec.update(source="County of San Diego DEHQ (sdbeachinfo.com)", source_url=SD_URL)
            if sd:
                ss = [dict(id=i, **sd["sites"][i]) for i in sp["sd_sites"] if i in sd["sites"]]
                rec["stations"] = ss
                rec["status"] = worst([s["status"] for s in ss])
                rec["status_updated"] = sd["updated"]
                bad = [s for s in ss if s["status"] in ("closed", "advisory")]
                rec["status_detail"] = "; ".join(f'{s["label"]}: {s["name"]}' for s in bad) or None
        elif c == "Los Angeles":
            rec.update(source="LA County Dept. of Public Health", source_url=LA_URL)
            if la_page and la_page["rain_advisory"]:
                rec["status"] = "advisory"
                rec["status_detail"] = f'County-wide rain advisory until {la_page["advisory_until"]}'
            if la_map:
                ss = []
                for code in sp.get("la_stations", []):
                    for nm, v in la_map["stations"].items():
                        if nm.startswith(code + " "):
                            ss.append(dict(id=code, name=nm, color=v["color"], status=v["status"]))
                rec["stations"] = ss
                rec["status_updated"] = la_map["updated_label"]
                if rec["status"] == "unknown":
                    rec["status"] = worst([s["status"] for s in ss])
                if rec["status"] == "unknown" and ss:
                    rec["status_detail"] = "DPH map shows no current result for these stations (results pending)"
        elif c == "Orange":
            rec.update(source="OC Health Care Agency (ocbeachinfo.com)", source_url=OC_URL)
            if oc:
                hits = []
                for kind, txt in (("closed", oc["closures"]), ("advisory", oc["warnings"]), ("advisory", oc["advisories"])):
                    for kw in sp.get("oc_keywords", []):
                        if txt and kw.lower() in txt.lower():
                            hits.append((kind, kw))
                rec["status"] = worst([h[0] for h in hits]) if hits else "open"
                rec["status_detail"] = ("Posting listed near " + ", ".join(sorted({h[1] for h in hits}))) if hits else \
                    "No closures, warnings or advisories listed by OC Health Care Agency for this area"
                rec["status_updated"] = iso(NOW)
        elif c in ("Ventura", "Santa Barbara"):
            vcsb = c == "Ventura"
            rec.update(source="Ventura County Environmental Health" if vcsb else
                       "Santa Barbara County Environmental Health", source_url=VC_URL if vcsb else SB_URL)
            feed, ids = (vc, sp.get("vc_stations", [])) if vcsb else (sb, sp.get("sb_stations", []))
            if feed:
                ss = [dict(id=i, **feed["sites"][i]) for i in ids if i in feed["sites"]]
                rec["stations"] = ss
                rec["status"] = worst([x["status"] for x in ss])
                rec["status_updated"] = feed["updated"] if ss else None
                if rec["status"] != "unknown":
                    rec["status_detail"] = "; ".join(f'{x["name"]}: {x["label"]}' for x in ss
                                                     if x["status"] == rec["status"])
        else:
            rec.update(source="County of San Diego DEHQ (sdbeachinfo.com)", source_url=SD_URL)
            rec["status_detail"] = "Not in the county's beach monitoring list"
        # ---- Heal the Bay grade (latest sample grade)
        cands = [htb[i] for i in sp.get("htb", []) if i in htb]
        if not cands and htb:
            near = sorted((km(sp["lat"], sp["lon"], h["lat"], h["lon"]), h["id"]) for h in htb.values()
                          if h["active"] and h.get("grade_updated"))
            cands = [htb[i] for d, i in near[:3] if d < 2.0]
        g = next((h for h in cands if h.get("dry_grade") and h["dry_grade"] not in ("ns", None)), None)
        g = g or (cands[0] if cands else None)
        rec["grade"] = dict(dry=g["dry_grade"], wet=g["wet_grade"], updated=g["grade_updated"],
                            site=g["title"], id=g["id"]) if g else None
        # ---- water temp
        best = sorted((km(sp["lat"], sp["lon"], t["lat"], t["lon"]), sid) for sid, t in temps.items())
        if best and best[0][0] < 80:
            d, sid = best[0]
            t = temps[sid]
            rec["water_temp_f"] = t["f"]
            rec["temp_source"] = f'NOAA NDBC {sid.upper()} – {t["name"]}'
            rec["temp_station"] = sid.upper()
            rec["temp_distance_km"] = round(d, 1)
            rec["temp_time"] = t["time"]
        else:
            rec.update(water_temp_f=None, temp_source=None, temp_station=None, temp_distance_km=None, temp_time=None)
        rec["wear"], rec["wear_key"] = wear(rec["water_temp_f"])
        # ---- rain
        rn = rain.get(c)
        rec["rain"] = rn
        rec["rain_flag"] = bool(rn and rn["rain_flag"])
        out.append(rec)

    counts = {k: sum(1 for r in out if r["status"] == k) for k in SEVERITY}
    doc = dict(generated=iso(NOW), spot_count=len(out), status_counts=counts, sources=sources,
               county_notes=dict(
                   la=dict(page=la_page, map_updated=la_map and la_map["updated_label"], map_colors=la_map and la_map["colors"]),
                   oc=oc, vc=vc and dict(updated=vc["updated"]), sb=sb and dict(updated=sb["updated"]), sd=sd and dict(updated=sd["updated"], counts=sd["counts"]), rain=rain),
               spots=out)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1))
    print(json.dumps(dict(spots=len(out), status_counts=counts,
                          sources={k: v["ok"] for k, v in sources.items()}), indent=1))


if __name__ == "__main__":
    main()
