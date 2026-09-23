"""
Loads the raw CSVs and builds the derived metrics used across the app.

All raw numbers come from company filings (see data/*.csv -> source column).
Anything computed here is my own derivation, and the formula sits next to it.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"

QUARTERS = [
    "Q1FY24", "Q2FY24", "Q3FY24", "Q4FY24",
    "Q1FY25", "Q2FY25", "Q3FY25", "Q4FY25",
    "Q1FY26", "Q2FY26", "Q3FY26", "Q4FY26",
    "Q1FY27",
]
DAYS_IN_Q = 91

COLORS = {
    "Blinkit": "#2a78d6",
    "Instamart": "#eb6834",
    "Zepto": "#1baf7a",
    "Other": "#a3a29c",
}

# Q4FY24 exit store count for Instamart (Swiggy Q3FY25 letter). Needed so Q1FY25 has an opening balance.
OPENING_STORES = {"Instamart": 523}


def load_raw():
    panel = pd.read_csv(DATA / "qcom_quarterly_panel.csv", parse_dates=["period_end"])
    zepto_q = pd.read_csv(DATA / "zepto_quarterly.csv", parse_dates=["period_end"])
    zepto_y = pd.read_csv(DATA / "zepto_annual.csv")
    guide = pd.read_csv(DATA / "management_guidance.csv")
    context = pd.read_csv(DATA / "industry_context.csv", parse_dates=["as_of"])
    vals = pd.read_csv(DATA / "valuations.csv", parse_dates=["as_of"])
    events = pd.read_csv(DATA / "events.csv", parse_dates=["date"])
    return panel, zepto_q, zepto_y, guide, context, vals, events


def _avg_stores(s, platform):
    prev = s.shift()
    if platform in OPENING_STORES:
        prev = prev.fillna(OPENING_STORES[platform])
    return (s + prev) / 2


def build_long(panel, zepto_q):
    """One tidy table: platform x quarter with every metric the app uses."""
    frames = []
    for plat, d in panel.groupby("platform"):
        d = d.sort_values("period_end").copy()
        d["avg_stores"] = _avg_stores(d.stores_end, plat)
        d["value_cr"] = d.nov_cr                     # NOV for Blinkit / Instamart
        d["value_label"] = "NOV"
        d["orders_per_store_day"] = np.where(
            d.orders_per_store_day.notna(), d.orders_per_store_day,
            d.orders_mn * 1e6 / (d.avg_stores * DAYS_IN_Q))
        d["freq_per_month"] = d.orders_mn / (d.mtu_mn * 3)
        d["ebitda_pct"] = d.adj_ebitda_cr / d.nov_cr * 100
        d["cm_pct"] = d.contribution_cr / d.nov_cr * 100
        d["fixed_cr"] = d.contribution_cr - d.adj_ebitda_cr
        d["fixed_per_store_day_k"] = d.fixed_cr * 1e7 / (d.avg_stores * DAYS_IN_Q) / 1e3
        frames.append(d)

    z = zepto_q.sort_values("period_end").copy()
    z["avg_stores"] = _avg_stores(z.stores_end, "Zepto")
    z["value_cr"] = z.nrv_cr                          # Zepto only discloses NRV (includes ads + fees)
    z["value_label"] = "NRV"
    z["ebitda_pct"] = z.adj_ebitda_pct_nrv
    frames.append(z)

    df = pd.concat(frames, ignore_index=True, sort=False)
    df["value_per_order"] = df.value_cr * 1e7 / (df.orders_mn * 1e6)
    df["value_per_store_day_lakh"] = df.value_cr * 1e7 / (df.avg_stores * DAYS_IN_Q) / 1e5
    # use Zepto's reported per-order figure where it exists, otherwise compute it
    df["ebitda_per_order"] = df.adj_ebitda_cr * 1e7 / (df.orders_mn * 1e6)
    df["ebitda_per_order"] = df.adj_ebitda_per_order_inr.fillna(df.ebitda_per_order)
    df["cm_per_order"] = df.contribution_cr * 1e7 / (df.orders_mn * 1e6)
    df["fixed_per_order"] = df.fixed_cr * 1e7 / (df.orders_mn * 1e6)
    df["quarter"] = pd.Categorical(df.quarter, QUARTERS, ordered=True)
    return df.sort_values(["platform", "quarter"]).reset_index(drop=True)


def growth_decomposition(d, q0, q1):
    """
    NOV = MTU x (orders per user per month x 3) x net AOV.
    Log growth splits additively; I scale each log share back to percentage points of total growth.
    """
    a, b = d.loc[q0], d.loc[q1]
    parts = {
        "Users": np.log(b.mtu_mn / a.mtu_mn),
        "Frequency": np.log(b.freq_per_month / a.freq_per_month),
        "Basket": np.log(b.value_per_order / a.value_per_order),
    }
    total_log = np.log(b.nov_cr / a.nov_cr)
    total_pct = (np.exp(total_log) - 1) * 100
    return {k: v / total_log * total_pct for k, v in parts.items()}, total_pct


def instamart_ebitda(mtu_mn, freq, basket, cm_pct, fixed_cr, extra_cost_per_order=0.0):
    """Quarterly Adj. EBITDA for the simulator. Returns a dict so the UI can show the pieces."""
    orders = mtu_mn * 1e6 * freq * 3
    nov_cr = orders * basket / 1e7
    contribution = nov_cr * cm_pct / 100 - orders * extra_cost_per_order / 1e7
    ebitda = contribution - fixed_cr
    return {
        "orders_mn": orders / 1e6,
        "nov_cr": nov_cr,
        "contribution_cr": contribution,
        "ebitda_cr": ebitda,
        "ebitda_per_order": ebitda * 1e7 / orders,
        "annual_nov_cr": nov_cr * 4,
    }


def fmt_inr(v, dec=0, unit=""):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    sign = "−" if v < 0 else ""
    return f"{sign}₹{abs(v):,.{dec}f}{unit}"
