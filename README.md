# Chipotle Mexican Grill (NYSE: CMG) — Equity Research Project

**Rating: SELL · Price target: $28 (~15% downside from $32.91, Nov 2, 2026)**
**Thesis: "Priced for perfection" — the current share price already reflects the bull case.**

An end-to-end equity research project built from public filings: a fast-casual industry deep dive, a DCF and trading comps valuation model, a 10-slide stock pitch, and a Python data pipeline that refreshes the model with one command.

---

## Key findings

| | Bull | Base | Bear |
|---|---|---|---|
| Price target | $33.65 | $28.19 | $21.29 |
| vs current price | +2% | −14% | −35% |
| Probability | 25% | 50% | 25% |

- **Probability-weighted value: $27.83 (−15%)** → asymmetric risk/reward skewed to the downside
- CMG trades at **19.5x EV/EBITDA vs a 16.8x peer median** (16% premium)
- Food and labor take **54% of every sales dollar**; Q3 2026 operating margin fell 2.2 pts to 13.7%
- Fast-casual growth slowed from ~9% to ~6% in 2025, driven by new units rather than traffic

---

## What's in this repo

| File | Description |
|---|---|
| [`CMG_Historicals_Assumptions.xlsx`](CMG_Historicals_Assumptions.xlsx) | Full valuation model (10 tabs) |
| [`US Fast-Casual Restaurant Industry Deep Dive.pdf`](<US Fast-Casual Restaurant Industry Deep Dive.pdf>) | US fast-casual industry report |
| [`Chipotle (CMG) Stock Pitch.pdf`](<Chipotle (CMG) Stock Pitch.pdf>) | 10-slide investment pitch |
| [`data-pipeline/`](data-pipeline/) | Python pipeline that refreshes the model and builds a quarterly dashboard |

### Model structure

1. **IS / BS / CF** — 5 years of historicals (FY2021–FY2025) parsed from SEC 10-K XBRL filings, with tie-out checks against reported totals
2. **Assumptions** — revenue growth, cost ratios, capex, working capital; historical ratios + FY2026E–FY2030E projections with written rationale
3. **Scenarios** — bull / base / bear switch driving the whole model, plus probability-weighted price target
4. **UFCF** — unlevered free cash flow build: EBIT × (1 − t) + D&A − Capex − ΔNWC
5. **WACC** — CAPM cost of equity (Rf 4.96%, β 0.96, ERP 4.23%); no funded debt → WACC ≈ 9.0%
6. **DCF** — mid-year convention, stub period, normalized terminal year, Gordon growth and exit-multiple terminal values, sensitivity tables
7. **Comps** — 7 restaurant peers (MCD, YUM, DPZ, WING, SHAK, CAVA, SG) on EV/EBITDA, EV/Revenue, P/E; valuation summary (football field)

### Data pipeline

Every quarter the model's market and filing inputs go stale, and re-copying them by hand for CMG and 7 peers is slow and error-prone. [`data-pipeline/`](data-pipeline/) automates it:

- Pulls the latest 10-K / 10-Q figures for all 8 companies from the **SEC XBRL API** and computes TTM revenue and EBITDA
- Fetches share prices and market caps with **yfinance**, so every comps row is refreshed on the same day
- Writes the new inputs into the model's Comps, WACC and DCF tabs with **openpyxl** (dated backup first, formulas untouched)
- Builds a **Plotly** dashboard: quarterly revenue and growth, same-store sales, margins, cost ratios, EV/EBITDA vs peers

```bash
cd data-pipeline
python run_all.py
```

See [`data-pipeline/README.md`](data-pipeline/README.md) for setup and design notes.

### Industry research covers

Market size & growth · value chain · key players · Porter's Five Forces · regulation & trends (wage laws, beef inflation, value wars, GLP-1 drugs, delivery) · profit pool · implications for the DCF assumptions

---

## Methodology notes

- **Operating leases are not treated as debt in the DCF**: rent is already deducted in EBIT (occupancy cost), so adding leases to debt would double-count. In the Comps tab, debt includes lease liabilities for every company so peers are measured on the same basis
- **Terminal year normalized**: capex scaled down from 5.5% to ~4.1% of revenue so that reinvestment matches a 3% perpetual growth rate
- **Share data split-adjusted** for the 50-for-1 stock split (June 2024)
- Color convention: blue = hard-coded inputs, black = formulas, green = cross-sheet links, yellow = assumption cells

## Data sources

Chipotle FY2023 & FY2025 Form 10-K and Q3 2026 Form 10-Q (SEC EDGAR) · SEC XBRL API and Yahoo Finance (data pipeline) · Q3 2026 earnings release · Technomic (via Restaurant Business, NRN) · Black Box Intelligence · Damodaran (ERP) · TipRanks (peer multiples) · Trading Economics (10Y Treasury)

Market data as of early November 2026.

---

*This is a student project for educational purposes only and is not investment advice.*
