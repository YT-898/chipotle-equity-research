"""Build the comps table and write the new inputs into the Excel model."""
import os
import shutil
from datetime import date, datetime

import pandas as pd
from openpyxl import load_workbook

from . import config, market, sec

T = config.TAGS


def _sum(*vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) if vals else None


def fundamentals(facts):
    """Every figure the comps table needs, in $ millions (shares in millions)."""
    rev, rev_end = sec.ttm(facts, T["revenue"])
    ebit, _ = sec.ttm(facts, T["ebit"])
    da, _ = sec.ttm(facts, T["da"])
    eps, _ = sec.ttm(facts, T["eps_diluted"], unit="USD/shares")
    cash, bs_date = sec.latest_instant(facts, T["cash"])

    def bal(key):
        """Latest balance-sheet value, ignored if it is older than the latest balance sheet (stale tag)."""
        v, d = sec.latest_instant(facts, T[key])
        if v is None or (bs_date and d and (date.fromisoformat(bs_date) - date.fromisoformat(d)).days > 100):
            return None
        return v

    st_inv, lt_inv = bal("st_investments"), bal("lt_investments")
    # Companies tag debt differently (one total line, or non-current + current, sometimes with
    # finance leases folded in). Every candidate below can only understate total debt, never
    # overstate it, so the largest one is the most complete.
    # Some companies (e.g. Yum) tag the current portion of long-term debt as "short-term
    # borrowings", so short-term borrowings are only added when no current-portion tag exists,
    # otherwise the same line would be counted twice.
    current = bal("debt_current")
    if current is None:
        current = bal("short_borrowings")
    candidates = [
        bal("debt_total"),
        _sum(bal("debt_noncurrent"), current),
    ]
    candidates = [c for c in candidates if c is not None]
    debt = max(candidates) if candidates else None
    if debt is not None and bal("finance_lease") and not sec.latest_instant(
            facts, ["LongTermDebtAndCapitalLeaseObligations"])[0]:
        debt += bal("finance_lease")
    lease = bal("lease_total")
    if lease is None:
        lease = _sum(bal("lease_current"), bal("lease_noncurrent"))

    dil, _ = sec.latest_share_count(facts, T["diluted_shares"])

    m = lambda v: None if v is None else v / 1e6
    return {
        "revenue_ttm": m(rev), "ebit_ttm": m(ebit), "da_ttm": m(da),
        "ebitda_ttm": m(_sum(ebit, da)) if ebit is not None and da is not None else None,
        "eps_ttm": eps, "cash": m(cash), "st_investments": m(st_inv), "lt_investments": m(lt_inv),
        "debt_ex_leases": m(debt), "operating_leases": m(lease),
        "debt_incl_leases": m(_sum(debt, lease)), "diluted_shares": m(dil),
        "period_end": rev_end, "balance_sheet_date": bs_date,
    }


def _market_cap(q, sec_diluted_shares):
    """Market cap in $ millions, cross-checked three ways because any single source can be garbage
    (Yahoo has returned ~0 for McDonald's): Yahoo's figure, price × Yahoo shares, price × SEC
    diluted shares. Near-zero values are dropped; with three left the median wins, with two that
    disagree by more than 50% the SEC-based figure wins."""
    yahoo = q["market_cap"] / 1e6 if q.get("market_cap") else None
    yahoo_shares = q["price"] * q["shares"] / 1e6 if q.get("shares") else None
    sec_based = q["price"] * sec_diluted_shares if sec_diluted_shares else None
    vals = [v for v in (yahoo, yahoo_shares, sec_based) if v and v > 1]
    if not vals:
        return None
    if len(vals) == 3:
        return sorted(vals)[1]
    if len(vals) == 2 and max(vals) / min(vals) > 1.5:
        return sec_based if sec_based in vals else max(vals)
    return vals[0]


def build_table(use_cache=True):
    rows = []
    for c in config.COMPANIES:
        cik = c["cik"] or sec.resolve_cik(c["ticker"])
        f = fundamentals(sec.company_facts(cik, use_cache))
        q = market.quote(c["ticker"])
        mcap = _market_cap(q, f["diluted_shares"])
        f.update({"ticker": c["ticker"], "name": c["name"], "price": q["price"], "market_cap": mcap})
        f["cash_and_st"] = _sum(f["cash"], f["st_investments"])
        f["ev"] = f["market_cap"] + (f["debt_incl_leases"] or 0) - (f["cash_and_st"] or 0) if f["market_cap"] else None
        f["ev_ebitda"] = f["ev"] / f["ebitda_ttm"] if f["ev"] and f["ebitda_ttm"] and f["ebitda_ttm"] > 0 else None
        # P/E is "NM" when EPS is negative, or when operating EBITDA is negative: then any positive
        # EPS comes from one-off gains (e.g. an asset sale), not from the business.
        ok = f["eps_ttm"] and f["eps_ttm"] > 0 and (f["ebitda_ttm"] is None or f["ebitda_ttm"] > 0)
        f["pe"] = f["price"] / f["eps_ttm"] if ok else None
        rows.append(f)
        print(f"  {c['ticker']:5} mkt cap {f['market_cap'] or 0:>9,.0f}  debt incl. leases {f['debt_incl_leases'] or 0:>8,.0f}  "
              f"(debt {f['debt_ex_leases'] or 0:,.0f} + leases {f['operating_leases'] or 0:,.0f})")
        print(f"  {'':5} revenue TTM {f['revenue_ttm'] or 0:>10,.0f}  EBITDA TTM {f['ebitda_ttm'] or 0:>9,.0f}  "
              f"EV/EBITDA {f['ev_ebitda'] or float('nan'):5.1f}x  (data to {f['period_end']})")
    df = pd.DataFrame(rows).set_index("ticker")
    return df


def update_model(df, model_path):
    """Write the fresh inputs into the blue input cells of the model. Formulas are left untouched."""
    if not os.path.exists(model_path):
        print(f"  Model not found at {model_path}; skipped Excel update.")
        return None
    # Timestamped so running twice in one day never overwrites an earlier backup.
    stem = model_path.replace(".xlsx", f"_backup_{datetime.now():%Y-%m-%d_%H%M%S}")
    backup, n = stem + ".xlsx", 1
    while os.path.exists(backup):
        n += 1
        backup = f"{stem}_{n}.xlsx"
    shutil.copy(model_path, backup)
    wb = load_workbook(model_path)
    ws = wb["Comps"]
    today = date.today().isoformat()
    for r in range(6, 20):
        tk = ws[f"B{r}"].value
        if tk not in df.index:
            continue
        x = df.loc[tk]
        ws[f"D{r}"] = today
        if tk != "CMG" and pd.notna(x["market_cap"]):
            ws[f"E{r}"] = round(float(x["market_cap"]), 2)  # CMG's market cap is a formula linked to the WACC tab
        for col, key in (("F", "debt_incl_leases"), ("G", "cash_and_st"), ("I", "ebitda_ttm"), ("J", "revenue_ttm")):
            if pd.notna(x[key]):
                ws[f"{col}{r}"] = round(float(x[key]), 2)
        ws[f"O{r}"] = round(float(x["pe"]), 1) if pd.notna(x["pe"]) else "NM"
    ws["A2"] = ("$ in millions. Source: SEC XBRL filings (TTM revenue / EBITDA, latest cash, debt and lease "
                "liabilities; 'debt' INCLUDES lease liabilities) + Yahoo Finance market data, via data-pipeline. "
                "EV recomputed here = Market cap + Debt − Cash for every company.")
    ws["A3"] = f"All rows refreshed on the same day ({today}) by data-pipeline/run_all.py."
    ws["E42"] = f"Latest close as of {today}"
    cmg = df.loc["CMG"]
    wb["WACC"]["B17"] = round(float(cmg["price"]), 2)
    dcf = wb["DCF"]
    dcf["B11"] = round(float(_sum(cmg["cash"], cmg["st_investments"], cmg["lt_investments"])), 1)
    if pd.notna(cmg["diluted_shares"]):
        dcf["B13"] = round(float(cmg["diluted_shares"]), 1)
    dcf["B5"] = date.fromisoformat(cmg["balance_sheet_date"])
    wb.calculation.fullCalcOnLoad = True  # Excel recalculates every formula when you open the file
    wb.save(model_path)
    print(f"  Updated {model_path} (backup saved as {os.path.basename(backup)})")
    return backup
