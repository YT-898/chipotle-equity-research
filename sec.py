"""Download and read SEC XBRL 'company facts' (the same numbers that are in 10-K / 10-Q filings)."""
import json
import os
import time
from datetime import date, timedelta

import requests

from . import config

BASE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
CACHE_DIR = os.path.join(config.OUTPUT_DIR, "sec_cache")


def _get(url):
    if "example.com" in config.USER_AGENT or "Your Name" in config.USER_AGENT:
        raise SystemExit("Create cmg_pipeline/config_local.py with one line: USER_AGENT = \"Your Name your@email.com\" (the SEC requires it).")
    r = requests.get(url, headers={"User-Agent": config.USER_AGENT, "Accept-Encoding": "gzip, deflate"}, timeout=30)
    r.raise_for_status()
    time.sleep(0.2)  # SEC allows max 10 requests per second; stay well below
    return r.json()


def resolve_cik(ticker):
    data = _get(TICKERS_URL)
    for row in data.values():
        if row["ticker"].upper() == ticker.upper():
            return int(row["cik_str"])
    raise ValueError(f"CIK not found for {ticker}")


def company_facts(cik, use_cache=True):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{cik}.json")
    today = date.today().isoformat()
    if use_cache and os.path.exists(path):
        with open(path) as f:
            cached = json.load(f)
        if cached.get("_downloaded") == today:
            return cached
    facts = _get(BASE.format(cik=cik))
    facts["_downloaded"] = today
    with open(path, "w") as f:
        json.dump(facts, f)
    return facts


# ---------- reading the facts ----------

def _days(e):
    if "start" not in e:
        return 0
    return (date.fromisoformat(e["end"]) - date.fromisoformat(e["start"])).days


def _entries_for_tag(pool, tag, unit):
    units = pool[tag]["units"]
    u = unit or ("USD" if "USD" in units else next(iter(units)))
    if u not in units:
        return []
    best = {}
    for e in units[u]:
        if e.get("form") not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        key = (e.get("start"), e["end"])
        if key not in best or e["filed"] > best[key]["filed"]:
            best[key] = e
    return sorted(best.values(), key=lambda e: (e["end"], _days(e)))


def entries_by_recency(facts, tags, unit=None, taxonomy="us-gaap"):
    """[(tag, entries)] for every tag that has data, most recently reported tag first.

    Companies switch XBRL tags over the years. A tag used only in old filings would otherwise
    hand back a stale value, so the tag with the newest period wins (list order breaks ties)."""
    pool = facts.get("facts", {}).get(taxonomy, {})
    found = []
    for i, tag in enumerate(tags):
        if tag in pool:
            es = _entries_for_tag(pool, tag, unit)
            if es:
                found.append((max(e["end"] for e in es), -i, tag, es))
    found.sort(reverse=True)
    return [(tag, es) for _, _, tag, es in found]


def entries(facts, tags, unit=None, taxonomy="us-gaap"):
    """All reported values for the most recently used tag, de-duplicated by period (latest filing wins)."""
    found = entries_by_recency(facts, tags, unit, taxonomy)
    return found[0] if found else (None, [])


def latest_instant(facts, tags):
    """Most recent balance-sheet value (a point in time)."""
    tag, es = entries(facts, tags)
    es = [e for e in es if "start" not in e]
    if not es:
        return None, None
    e = max(es, key=lambda e: e["end"])
    return e["val"], e["end"]


def _is_annual(e):
    return 350 <= _days(e) <= 380


def ttm(facts, tags, unit=None):
    """Trailing twelve months = last fiscal year + current year-to-date − prior year-to-date.
    Tries the most recently used tag first and falls back to the next one if it has no annual figure."""
    for _, es in entries_by_recency(facts, tags, unit):
        result = _ttm_from(es)
        if result[0] is not None:
            return result
    return None, None


def _ttm_from(es):
    flows = [e for e in es if "start" in e]
    annual = [e for e in flows if _is_annual(e)]
    if not annual:
        return None, None
    a = max(annual, key=lambda e: e["end"])
    a_end = date.fromisoformat(a["end"])
    ytd = [e for e in flows if not _is_annual(e) and date.fromisoformat(e["end"]) > a_end
           and date.fromisoformat(e["start"]) > a_end - timedelta(days=20)]
    if not ytd:
        return a["val"], a["end"]
    y = max(ytd, key=lambda e: (e["end"], _days(e)))
    y_end, d = date.fromisoformat(y["end"]), _days(y)
    prior = [e for e in flows if abs((y_end - date.fromisoformat(e["end"])).days - 365) <= 10 and abs(_days(e) - d) <= 10]
    if not prior:
        return a["val"], a["end"]
    p = max(prior, key=lambda e: e["filed"])
    return a["val"] + y["val"] - p["val"], y["end"]


def quarterly(facts, tags, unit=None):
    """Quarterly series {period_end: value}. Q4 is derived as full year − first nine months."""
    tag, es = entries(facts, tags, unit)
    flows = [e for e in es if "start" in e]
    q = {e["end"]: e["val"] for e in flows if 80 <= _days(e) <= 100}
    for a in (e for e in flows if _is_annual(e)):
        if a["end"] in q:
            continue
        nine = [e for e in flows if e["start"] == a["start"] and 260 <= _days(e) <= 285]
        if nine:
            q[a["end"]] = a["val"] - max(nine, key=lambda e: e["end"])["val"]
    return dict(sorted(q.items()))
