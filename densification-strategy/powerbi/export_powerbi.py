"""
Writes the tables the Power BI dashboard loads, all from model.py so the
dashboard and the deck can't disagree.

    python export_powerbi.py

Output goes to powerbi/data/. Money columns are in ₹ unless the name says Cr.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import model  # noqa: E402

OUT = HERE / "data"
QUARTERS = ["Q1FY25", "Q2FY25", "Q3FY25", "Q4FY25", "Q1FY26", "Q2FY26", "Q3FY26", "Q4FY26", "Q1FY27"]
PLATFORMS = {"Blinkit": "#2A78D6", "Instamart": "#EB6834"}


def quarters():
    end = {"Q1": "06-30", "Q2": "09-30", "Q3": "12-31", "Q4": "03-31"}
    rows = []
    for k, q in enumerate(QUARTERS, start=1):
        fy = int(q[-2:])
        year = 2000 + (fy if q[:2] == "Q4" else fy - 1)
        rows.append(dict(Quarter=q, QuarterEnd=f"{year}-{end[q[:2]]}", SortOrder=k, FiscalYear=f"FY{fy}"))
    return pd.DataFrame(rows)


def quarterly(df):
    """Additive columns only. Every ratio is a DAX measure, so it stays right at any level of filtering."""
    d = df[df.platform.isin(PLATFORMS) & df.quarter.astype(str).isin(QUARTERS)].copy()
    d["StoreDays"] = d.avg_stores * model.m.DAYS_IN_Q
    d["UserMonths_Mn"] = d.mtu_mn * 3
    out = d.rename(columns={
        "platform": "Platform", "quarter": "Quarter", "nov_cr": "NOV_Cr", "orders_mn": "Orders_Mn",
        "mtu_mn": "MTU_Mn", "stores_end": "StoresEnd", "avg_stores": "AvgStores",
        "contribution_cr": "Contribution_Cr", "adj_ebitda_cr": "AdjEBITDA_Cr", "fixed_cr": "HQFixed_Cr",
    })[["Platform", "Quarter", "NOV_Cr", "Orders_Mn", "MTU_Mn", "UserMonths_Mn", "StoresEnd", "AvgStores",
        "StoreDays", "Contribution_Cr", "AdjEBITDA_Cr", "HQFixed_Cr"]]
    out["Quarter"] = out.Quarter.astype(str)
    return out.round(4)


def baseline(i):
    s = model.store_pnl(i)
    a = model.ASSUMPTIONS
    return pd.DataFrame([dict(
        Quarter=model.BASE_Q,
        Stores=int(i.stores_end),
        StoreNOV_Day=round(s["nov"], 2),
        StoreOrders_Day=round(s["orders"], 2),
        NetAOV=round(s["aov"], 4),
        CM_Pct=round(i.cm_pct / 100, 6),                 # fraction of NOV
        HQFixed_Day=round(s["fixed"], 2),
        StoreSD=a["store_nov_sd_lakh"] * 1e5,
        CapexPerStore_Cr=a["capex_per_store_cr"],
        Utilisation_Pct=40.0,
        BreakevenNOV_Cr=60_000,
        AnnualEBITDALoss_Cr=round(-i.adj_ebitda_cr * 4, 2),
        BlinkitTargetNOV_Day=11e5,
    )])


def per_order_gap(i, b):
    g = model.per_order_gap(i, b)
    rows = [("Blinkit", g["Blinkit"], "Start"),
            ("HQ & tech costs over fewer orders", g["HQ costs over fewer orders"], "Volume"),
            ("Store rent & staff over fewer orders", g["Store costs over fewer orders"], "Volume"),
            ("Ads, 1P margin, pricing", g["Variable margin (ads, 1P, pricing)"], "Margin")]
    return pd.DataFrame([dict(Step=n, Rs_per_Order=round(v, 2), Kind=k, SortOrder=j + 1)
                         for j, (n, v, k) in enumerate(rows)])


def throughput(i, b):
    t = model.throughput_gap(i, b)
    rows = []
    for k, (metric, iv, bv) in enumerate([
            ("Users per store", t["i_users"], t["b_users"]),
            ("Orders per user per month", i.freq_per_month, b.freq_per_month),
            ("Orders per store per day", t["i_orders"], t["b_orders"])], start=1):
        rows += [dict(Metric=metric, Platform="Instamart", Value=round(iv, 3), SortOrder=k),
                 dict(Metric=metric, Platform="Blinkit", Value=round(bv, 3), SortOrder=k)]
    return pd.DataFrame(rows)


def plays(i):
    p = model.plan(i)
    sized = {n: (v, o) for n, v, o in p["stack"]}
    meta = {
        "Morning Ritual + fresh": (3.0, "Milk, bread, eggs, curd and a fruit-and-veg box on a 6-9 am batched slot; "
                                        "scale Nectr with a replacement promise", "Orders per user per month 2.83 to 3.08"),
        "Swiggy-to-Mart bridge": (4.45, "Offer tomorrow's milk on the Swiggy food-tracking screen; one cart, one fee",
                                  "8% of food-only users in a radius try Instamart"),
        "Win back the lapsed": (4.2, "Diagnose why each one-time user left and send the fix, not a blanket coupon",
                                "About 580 users per store back at 2 orders a month"),
        "Bigger basket": (3.4, "Private label, recipe add-ons, Maxxsaver thresholds set per store",
                          "Net AOV 508 to 523"),
    }
    rows = []
    for k, (name, (ease, what, target)) in enumerate(meta.items(), start=1):
        v, o = sized[name]
        rows.append(dict(Play=name, InPlan=True, Status="In the plan", Ease=ease, NOV_Day=round(v, 2),
                         Impact_k=round(v / 1e3, 1), OrdersAdded_Day=round(o, 3), What=what, Target=target, SortOrder=k))
    parked = [("Retune radius of under-used stores", 2.0, 15, "Parked", "Phase 2: needs rider and SLA work"),
              ("Afternoon fee holiday", 3.9, 7, "Parked", "Folded into the morning-slot test"),
              ("Blanket free delivery", 4.8, 31, "Rejected", "Margin-negative; rents demand; easy to copy"),
              ("Sub-10-minute promise", 1.0, 6, "Rejected", "Regulatory headwind since Jan-26"),
              ("New stores in served micro-markets", 2.2, -10, "Rejected", "Splits demand, lowers throughput")]
    for k, (name, ease, imp, status, why) in enumerate(parked, start=len(rows) + 1):
        rows.append(dict(Play=name, InPlan=False, Status=status, Ease=ease, NOV_Day=imp * 1e3, Impact_k=imp,
                         OrdersAdded_Day=0.0, What=why, Target="", SortOrder=k))
    return pd.DataFrame(rows)


def lever_stack(i):
    p = model.plan(i)
    rows = [dict(Step="Today", NOV_k=round(p["store"]["nov"] / 1e3, 2), SortOrder=1)]
    rows += [dict(Step=n, NOV_k=round(v / 1e3, 2), SortOrder=k) for k, (n, v, _) in enumerate(p["stack"], start=2)]
    return pd.DataFrame(rows)


def heart():
    rows = [
        ("Happiness", "People trust the morning and fresh orders", "Fewer complaints on fresh",
         "Fresh complaints per 1,000 orders; morning-slot CSAT", "Not public", "Below today; CSAT 4.5+"),
        ("Engagement", "Instamart becomes a daily app", "More orders and categories per user",
         "Orders per MTU per month", "2.83", "3.08"),
        ("Adoption", "The new behaviours get picked up", "Sign-ups and first orders",
         "% MTU on Morning Ritual; % food-only users trying Instamart", "0%; 0%", "8-10%; 8%"),
        ("Retention", "First-timers stay", "Users still ordering after a month",
         "M1 retention; day-60 survival of won-back users", "61%", "65%; 40%+"),
        ("Task success", "The order arrives complete and on time", "Fewer substitutions and misses",
         "Fill rate on top-200 SKUs; on-time % in 6-9 am slot", "Not public", "98%+; 95%+"),
        ("Guardrail", "Growth doesn't cost margin or riders", "Stop if breached",
         "Contribution per added order; peak-hour on-time %; rider earnings per hour",
         "", "20+ per order; no worse than control; no lower"),
    ]
    return pd.DataFrame([dict(Dimension=d, Goal=g, Signal=s, Metric=m_, Baseline=b, Target=t, SortOrder=k)
                         for k, (d, g, s, m_, b, t) in enumerate(rows, start=1)])


def five_whys(i, b):
    t = model.throughput_gap(i, b)
    rows = [
        ("Why do stores lose money?", "They sell 5.5 lakh a day; costs are set for 8 lakh+."),
        ("Why so little per store?", "1,089 orders a day against 1,552 at Blinkit, on the same basket."),
        ("Why so few orders?", f"Each user orders 2.83 times a month vs 3.47. Frequency is {t['freq_share']:.0%} of the gap."),
        ("Why so infrequent?", "It's a top-up app, not a daily one; 39% of new users don't return in month one."),
        ("Root cause", "316 stores opened in one quarter (Q4FY25) ahead of demand: ~40% utilisation."),
    ]
    return pd.DataFrame([dict(Step=k, Question=q, Answer=a) for k, (q, a) in enumerate(rows, start=1)])


def postscript():
    rows = [("Q1FY27", -20), ("Habit & reactivation pricing", -100), ("New-user & festive mix", -40),
            ("Fuller stores (orders/store +9.5%)", 60)]
    return pd.DataFrame([dict(Step=n, bps=v, SortOrder=k) for k, (n, v) in enumerate(rows, start=1)])


def main():
    OUT.mkdir(exist_ok=True)
    df, i, b, _ = model.baseline()
    tables = {
        "dim_quarter": quarters(),
        "dim_platform": pd.DataFrame([dict(Platform=p, Colour=c, SortOrder=k) for k, (p, c) in enumerate(PLATFORMS.items(), 1)]),
        "fact_quarterly": quarterly(df),
        "baseline": baseline(i),
        "per_order_gap": per_order_gap(i, b),
        "throughput": throughput(i, b),
        "plays": plays(i),
        "lever_stack": lever_stack(i),
        "heart": heart(),
        "five_whys": five_whys(i, b),
        "q2fy27_cm_bridge": postscript(),
    }
    for name, t in tables.items():
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name:18s} {len(t):3d} rows")
    return tables


if __name__ == "__main__":
    main()
