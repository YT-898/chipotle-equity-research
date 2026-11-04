"""One command to refresh everything:  python run_all.py

1. Downloads the latest 10-K / 10-Q numbers for Chipotle and 7 peers from the SEC
2. Gets current share prices and market caps
3. Writes the new inputs into the Excel model (Comps, WACC price, DCF cash and shares)
4. Builds output/cmg_dashboard.html
"""
import argparse
import os

from cmg_pipeline import comps, config, dashboard, market, sec


def main():
    ap = argparse.ArgumentParser(description="Refresh the Chipotle model and dashboard")
    ap.add_argument("--model", default=config.MODEL_PATH, help="path to CMG_Historicals_Assumptions.xlsx")
    ap.add_argument("--no-excel", action="store_true", help="do not modify the Excel model")
    ap.add_argument("--refresh", action="store_true", help="ignore today's cached SEC downloads")
    args = ap.parse_args()
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    print("1/3  Building comps table from SEC filings + market data ...")
    table = comps.build_table(use_cache=not args.refresh)
    csv_path = os.path.join(config.OUTPUT_DIR, "comps_latest.csv")
    table.round(3).to_csv(csv_path)
    print(f"  Comps table saved to {csv_path}")

    print("2/3  Updating the Excel model ...")
    if args.no_excel:
        print("  Skipped (--no-excel).")
    else:
        comps.update_model(table, args.model)

    print("3/3  Building the dashboard ...")
    cmg_cik = next(c["cik"] for c in config.COMPANIES if c["ticker"] == "CMG")
    dashboard.build(sec.company_facts(cmg_cik), market.history("CMG"), table)
    print("Done. Open the Excel model (it recalculates on open) and output/cmg_dashboard.html.")


if __name__ == "__main__":
    main()
