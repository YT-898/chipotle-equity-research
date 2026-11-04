# Chipotle Mexican Grill (NYSE: CMG) — Equity Research Project

**Rating: SELL · Price target: $28 (~15% downside from $32.91, Nov 2, 2026)**
**Thesis: "Priced for perfection" — the current share price already reflects the bull case.**

An end-to-end equity research project built from public filings: a fast-casual industry deep dive, a DCF and trading comps valuation model, and a 10-slide stock pitch.

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
| `01_DCF_Model/CMG_Historicals_Assumptions.xlsx` | Full valuation model (10 tabs) |
| `02_Industry_Research/Industry_Deep_Dive.pdf` | US fast-casual industry report |
| `03_Stock_Pitch/CMG_Stock_Pitch.pdf` | 10-slide investment pitch |

### Model structure

1. **IS / BS / CF** — 5 years of historicals (FY2021–FY2025) parsed from SEC 10-K XBRL filings, with tie-out checks against reported totals
2. **Assumptions** — revenue growth, cost ratios, capex, working capital; historical ratios + FY2026E–FY2030E projections with written rationale
3. **Scenarios** — bull / base / bear switch driving the whole model, plus probability-weighted price target
4. **UFCF** — unlevered free cash flow build: EBIT × (1 − t) + D&A − Capex − ΔNWC
5. **WACC** — CAPM cost of equity (Rf 4.96%, β 0.96, ERP 4.23%); no funded debt → WACC ≈ 9.0%
6. **DCF** — mid-year convention, stub period, normalized terminal year, Gordon growth and exit-multiple terminal values, sensitivity tables
7. **Comps** — 7 restaurant peers (MCD, YUM, DPZ, WING, SHAK, CAVA, SG) on EV/EBITDA, EV/Revenue, P/E; valuation summary (football field)

### Industry research covers

Market size & growth · value chain · key players · Porter's Five Forces · regulation & trends (wage laws, beef inflation, value wars, GLP-1 drugs, delivery) · profit pool · implications for the DCF assumptions

---

## Methodology notes

- **Operating leases are not treated as debt**: rent is already deducted in EBIT (occupancy cost), so adding leases to debt would double-count
- **Terminal year normalized**: capex scaled down from 5.5% to ~4.1% of revenue so that reinvestment matches a 3% perpetual growth rate
- **Share data split-adjusted** for the 50-for-1 stock split (June 2024)
- Color convention: blue = hard-coded inputs, black = formulas, green = cross-sheet links, yellow = assumption cells

## Data sources

Chipotle FY2023 & FY2025 Form 10-K and Q3 2026 Form 10-Q (SEC EDGAR) · Q3 2026 earnings release · Technomic (via Restaurant Business, NRN) · Black Box Intelligence · Damodaran (ERP) · TipRanks (peer multiples) · Trading Economics (10Y Treasury)

Market data as of early November 2026.

---

*This is a student project for educational purposes only and is not investment advice.*
