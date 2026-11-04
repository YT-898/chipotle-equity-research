"""Offline test: fake SEC + market data, real Excel model copy. Run: python tests/test_offline.py <model.xlsx>"""
import os
import shutil
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cmg_pipeline import comps, config, dashboard, market, sec  # noqa: E402


def flow(start, end, val, form="10-Q", filed=None, fp="Q"):
    return {"start": start, "end": end, "val": val, "form": form, "filed": filed or end, "fp": fp}


def inst(end, val, form="10-Q"):
    return {"end": end, "val": val, "form": form, "filed": end}


def fake_facts(scale=1.0):
    M = 1e6 * scale
    # FY2025 annual + quarterly and YTD for 2025 and 2026 (Q1-Q3)
    rev_q25 = [2880, 3060, 3000]; rev_q26 = [3100, 3350, 3300]; fy25 = 11925.6
    ebit_q25 = [440, 560, 470];   ebit_q26 = [460, 540, 452];   fy25e = 1935.8
    da_q25 = [88, 90, 91];        da_q26 = [96, 98, 100];        fy25d = 361.4
    def series(q25, q26, fy, fy24=None, prior_fy=None):
        es = [flow("2025-01-01", "2025-12-31", fy * M, "10-K", "2026-02-04", "FY")]
        if fy24:
            es.append(flow("2024-01-01", "2024-12-31", fy24 * M, "10-K", "2025-02-05", "FY"))
        ends = ["03-31", "06-30", "09-30"]; starts = ["01-01", "04-01", "07-01"]
        for yr, q in (("2025", q25), ("2026", q26)):
            ytd = 0
            for i, v in enumerate(q):
                es.append(flow(f"{yr}-{starts[i]}", f"{yr}-{ends[i]}", v * M))
                ytd += v
                if i:
                    es.append(flow(f"{yr}-01-01", f"{yr}-{ends[i]}", ytd * M))
        return es
    return {"facts": {"us-gaap": {
        "Revenues": {"units": {"USD": series(rev_q25, rev_q26, fy25, 11313.9)}},
        "OperatingIncomeLoss": {"units": {"USD": series(ebit_q25, ebit_q26, fy25e, 1916.3)}},
        "DepreciationDepletionAndAmortization": {"units": {"USD": series(da_q25, da_q26, fy25d)}},
        "CostDirectMaterial": {"units": {"USD": series([850, 905, 900], [915, 990, 974], 3527.0)}},
        "CostDirectLabor": {"units": {"USD": series([730, 760, 756], [790, 850, 848], 2991.7)}},
        "EarningsPerShareDiluted": {"units": {"USD/shares": [flow("2025-01-01", "2025-12-31", 1.14, "10-K", "2026-02-04", "FY"),
                                                             flow("2025-01-01", "2025-09-30", 0.85), flow("2026-01-01", "2026-09-30", 0.83)]}},
        "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [flow("2026-07-01", "2026-09-30", 1267.703e6)]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [inst("2025-12-31", 350.5 * M, "10-K"), inst("2026-09-30", 634.21 * M)]}},
        "MarketableSecuritiesCurrent": {"units": {"USD": [inst("2026-09-30", 268.354 * M)]}},
        "LongTermInvestments": {"units": {"USD": [inst("2026-09-30", 100.365 * M)]}},
        "OperatingLeaseLiabilityCurrent": {"units": {"USD": [inst("2026-09-30", 320 * M)]}},
        "OperatingLeaseLiabilityNoncurrent": {"units": {"USD": [inst("2026-09-30", 5280 * M)]}},
    }}}


def main(model):
    sec.company_facts = lambda cik, use_cache=True: fake_facts(1.0 if cik == 1058090 else 0.5)
    sec.resolve_cik = lambda t: 999
    market.quote = lambda t: {"price": 32.91 if t == "CMG" else 100.0, "market_cap": 41630e6 if t == "CMG" else 20000e6}
    idx = pd.date_range("2023-11-01", periods=150, freq="W")
    market.history = lambda t, **k: pd.Series(range(150), index=idx, dtype=float) / 3 + 25

    # TTM check: FY25 + YTD26 - YTD25
    f = fake_facts()
    v, end = sec.ttm(f, config.TAGS["revenue"])
    expect = (11925.6 + (3100 + 3350 + 3300) - (2880 + 3060 + 3000)) * 1e6
    assert abs(v - expect) < 1, (v, expect)
    assert end == "2026-09-30"
    q = sec.quarterly(f, config.TAGS["revenue"])
    assert abs(q["2025-12-31"] - (11925.6 - 8940) * 1e6) < 1, q.get("2025-12-31")
    print("TTM and Q4 derivation OK:", round(v / 1e6, 1), "Q4 2025:", round(q["2025-12-31"] / 1e6, 1))

    os.makedirs("output", exist_ok=True)
    test_model = os.path.join("output", "model_test_copy.xlsx")
    shutil.copy(model, test_model)
    table = comps.build_table()
    comps.update_model(table, test_model)
    dashboard.build(fake_facts(), market.history("CMG"), table, out_path=os.path.join("output", "dashboard_test.html"))
    print(table[["revenue_ttm", "ebitda_ttm", "debt_incl_leases", "cash_and_st", "ev_ebitda", "pe"]].round(2))


if __name__ == "__main__":
    main(sys.argv[1])
