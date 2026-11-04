"""Quarterly dashboard for Chipotle: revenue, margins, cost ratios, same-store sales and share price."""
import os
from datetime import date

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import config, sec

TERRA, MUSTARD, OLIVE, DARK, CREAM = "#8B3A2B", "#DDB65C", "#6E6440", "#231F1E", "#F1E6CC"
COMPS_CSV = os.path.join(os.path.dirname(__file__), "comps_manual.csv")


def quarterly_frame(facts):
    T = config.TAGS
    s = {k: sec.quarterly(facts, T[k]) for k in ("revenue", "ebit", "food_cost", "labor_cost")}
    df = pd.DataFrame(s)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().iloc[-16:]  # last 4 years
    df["revenue_b"] = df["revenue"] / 1e9
    df["yoy_growth"] = df["revenue"].pct_change(4)
    df["op_margin"] = df["ebit"] / df["revenue"]
    df["food_pct"] = df["food_cost"] / df["revenue"]
    df["labor_pct"] = df["labor_cost"] / df["revenue"]
    df["label"] = [f"Q{(d.month - 1) // 3 + 1} {d.year}" for d in df.index]
    return df


def build(facts, price_history, comps_table=None, out_path=None):
    q = quarterly_frame(facts)
    comps = pd.read_csv(COMPS_CSV) if os.path.exists(COMPS_CSV) else pd.DataFrame(columns=["quarter", "comps_pct"])

    fig = make_subplots(rows=3, cols=2, vertical_spacing=0.11, horizontal_spacing=0.08,
                        subplot_titles=("Quarterly revenue ($B) and YoY growth", "Same-store sales (comps)",
                                        "Operating margin", "Food and labor, % of revenue",
                                        "Share price (weekly close, $)", "EV/EBITDA vs peers"),
                        specs=[[{"secondary_y": True}, {}], [{}, {}], [{}, {}]])

    fig.add_bar(x=q["label"], y=q["revenue_b"], name="Revenue ($B)", marker_color=MUSTARD, row=1, col=1)
    fig.add_scatter(x=q["label"], y=q["yoy_growth"], name="YoY growth", mode="lines+markers",
                    line=dict(color=TERRA, width=3), row=1, col=1, secondary_y=True)
    fig.update_yaxes(tickformat=".1%", secondary_y=True, row=1, col=1)

    if len(comps):
        colors = [TERRA if v < 0 else OLIVE for v in comps["comps_pct"]]
        fig.add_bar(x=comps["quarter"], y=comps["comps_pct"] / 100, marker_color=colors, name="Comps",
                    text=[f"{v:+.1f}%" for v in comps["comps_pct"]], textposition="outside", row=1, col=2)
        fig.update_yaxes(tickformat=".0%", row=1, col=2)

    fig.add_scatter(x=q["label"], y=q["op_margin"], mode="lines+markers", name="Operating margin",
                    line=dict(color=TERRA, width=3), row=2, col=1)
    fig.update_yaxes(tickformat=".0%", row=2, col=1)

    fig.add_scatter(x=q["label"], y=q["food_pct"], mode="lines+markers", name="Food, beverage, packaging",
                    line=dict(color=MUSTARD, width=3), row=2, col=2)
    fig.add_scatter(x=q["label"], y=q["labor_pct"], mode="lines+markers", name="Labor",
                    line=dict(color=OLIVE, width=3), row=2, col=2)
    fig.update_yaxes(tickformat=".0%", row=2, col=2)

    if price_history is not None and len(price_history):
        fig.add_scatter(x=price_history.index, y=price_history.values, mode="lines", name="CMG price",
                        line=dict(color=DARK, width=2), row=3, col=1)

    if comps_table is not None and "ev_ebitda" in comps_table:
        ct = comps_table.dropna(subset=["ev_ebitda"]).sort_values("ev_ebitda")
        fig.add_bar(y=ct.index, x=ct["ev_ebitda"], orientation="h", name="EV/EBITDA",
                    marker_color=[TERRA if t == "CMG" else MUSTARD for t in ct.index],
                    text=[f"{v:.1f}x" for v in ct["ev_ebitda"]], textposition="outside", row=3, col=2)
        fig.update_xaxes(range=[0, float(ct["ev_ebitda"].max()) * 1.18], row=3, col=2)

    for tr in fig.data:
        tr.showlegend = tr.name in ("Food, beverage, packaging", "Labor", "YoY growth", "Revenue ($B)")
    fig.update_layout(height=1250, showlegend=True, paper_bgcolor=CREAM, plot_bgcolor="#FBF6EA",
                      font=dict(family="Arial", color=DARK, size=13), margin=dict(t=60, l=50, r=30, b=40),
                      legend=dict(orientation="h", y=-0.04))

    last = q.dropna(subset=["revenue"]).iloc[-1]
    kpis = [("Latest quarter", last["label"]), ("Revenue", f"${last['revenue_b']:.2f}B"),
            ("YoY growth", f"{last['yoy_growth']:+.1%}" if pd.notna(last["yoy_growth"]) else "n/a"),
            ("Operating margin", f"{last['op_margin']:.1%}" if pd.notna(last["op_margin"]) else "n/a")]
    if comps_table is not None and "CMG" in comps_table.index:
        kpis.append(("Share price", f"${comps_table.loc['CMG', 'price']:.2f}"))
    cards = "".join(f"<div class='k'><div class='l'>{a}</div><div class='v'>{b}</div></div>" for a, b in kpis)
    html = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Chipotle Dashboard</title><style>
body{{margin:0;background:{CREAM};font-family:Arial,sans-serif;color:{DARK}}}
header{{background:{TERRA};color:{CREAM};padding:24px 32px}} h1{{margin:0;font-size:28px}} p{{margin:6px 0 0;opacity:.9}}
.ks{{display:flex;flex-wrap:wrap;gap:16px;padding:20px 32px}} .k{{background:#E7D7B1;border-radius:12px;padding:14px 20px;min-width:160px}}
.l{{font-size:13px;color:#4A3F35}} .v{{font-size:26px;font-weight:bold;color:{TERRA}}} main{{padding:0 16px 32px}}
</style></head><body><header><h1>Chipotle Mexican Grill (CMG): quarterly dashboard</h1>
<p>Updated {date.today().isoformat()} · Fundamentals: SEC XBRL filings · Prices: Yahoo Finance · Comps: company earnings releases</p></header>
<div class='ks'>{cards}</div><main>{fig.to_html(full_html=False, include_plotlyjs='cdn')}</main></body></html>"""
    out_path = out_path or os.path.join(config.OUTPUT_DIR, "cmg_dashboard.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Dashboard saved to {out_path}")
    return out_path
