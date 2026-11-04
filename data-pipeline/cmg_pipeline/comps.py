"""Build the comps table and write the new inputs into the Excel model."""
import os
import shutil
from datetime import date

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
    st_inv, _ = sec.latest_instant(facts, T["st_investments"])
    lt_inv, _ = sec.latest_instant(facts, T["lt_investments"])

    debt, _ = sec.latest_instant(facts, T["debt_total"])
    if debt is None:
        debt = _sum(sec.latest_instant(facts, T["debt_noncurrent"])[0], sec.latest_instant(facts, T["debt_current"])[0])
    debt = _sum(debt, sec.latest_instant(facts, T["short_borrowings"])[0], sec.latest_instant(facts, T["finance_lease"])[0])
    lease, _ = sec.latest_instant(facts, T["lease_total"])
    if lease is None:
        lease = _sum(sec.latest_instant(facts, T["lease_current"])[0], sec.latest_instant(facts, T["lease_noncurrent"])[0])

    qs = sec.quarterly(facts, T["diluted_shares"], unit="shares")
    dil = list(qs.values())[-1] if qs else None

    m = lambda v: None if v is None else v / 1e6
    return {
        "revenue_ttm": m(rev), "ebit_ttm": m(ebit), "da_ttm": m(da),
        "ebitda_ttm": m(_sum(ebit, da)) if ebit is not None and da is not None else None,
        "eps_ttm": eps, "cash": m(cash), "st_investments": m(st_inv), "lt_investments": m(lt_inv),
        "debt_ex_leases": m(debt), "operating_leases": m(lease),
        "debt_incl_leases": m(_sum(debt, lease)), "diluted_shares": m(dil),
        "period_end": rev_end, "balance_sheet_date": bs_date,
    }


def build_table(use_cache=True):
    rows = []
    for c in config.COMPANIES:
        cik = c["cik"] or sec.resolve_cik(c["ticker"])
        f = fundamentals(sec.company_facts(cik, use_cache))
        q = market.quote(c["ticker"])
        f.update({"ticker": c["ticker"], "name": c["name"], "price": q["price"],
                  "market_cap": q["market_cap"] / 1e6 if q["market_cap"] else (q["price"] * f["diluted_shares"] if f["diluted_shares"] else None)})
        f["cash_and_st"] = _sum(f["cash"], f["st_investments"])
        f["ev"] = f["market_cap"] + (f["debt_incl_leases"] or 0) - (f["cash_and_st"] or 0) if f["market_cap"] else None
        f["ev_ebitda"] = f["ev"] / f["ebitda_ttm"] if f["ev"] and f["ebitda_ttm"] and f["ebitda_ttm"] > 0 else None
        f["pe"] = f["price"] / f["eps_ttm"] if f["eps_ttm"] and f["eps_ttm"] > 0 else None
        rows.append(f)
        print(f"  {c['ticker']:5} revenue TTM {f['revenue_ttm'] or 0:>10,.0f}  EBITDA TTM {f['ebitda_ttm'] or 0:>9,.0f}  "
              f"EV/EBITDA {f['ev_ebitda'] or float('nan'):5.1f}x  (data to {f['period_end']})")
    df = pd.DataFrame(rows).set_index("ticker")
    return df


def update_model(df, model_path):
    """Write the fresh inputs into the blue input cells of the model. Formulas are left untouched."""
    if not os.path.exists(model_path):
        print(f"  Model not found at {model_path}; skipped Excel update.")
        return None
    backup = model_path.replace(".xlsx", f"_backup_{date.today().isoformat()}.xlsx")
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
