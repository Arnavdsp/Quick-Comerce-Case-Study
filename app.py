"""
Quick commerce unit economics: Blinkit vs Instamart vs Zepto
Streamlit dashboard that goes with the notebook in this repo.

Run:  streamlit run app.py
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import metrics as m

st.set_page_config(page_title="Quick commerce unit economics", layout="wide")

COL = m.COLORS
PLOT_FONT = dict(family="Source Sans Pro, sans-serif", size=13, color="#31333F")


# ---------- data ----------
@st.cache_data
def get_data():
    panel, zepto_q, zepto_y, guide, context, vals, events = m.load_raw()
    df = m.build_long(panel, zepto_q)
    return df, panel, zepto_q, zepto_y, guide, context, vals, events


df, panel, zepto_q, zepto_y, guide, context, vals, events = get_data()
G = guide.set_index(["platform", "metric"]).value


def series(plat):
    return df[df.platform == plat].set_index("quarter")


B, I, Z = series("Blinkit"), series("Instamart"), series("Zepto")


def style(fig, height=360, ysuffix="", yprefix="", legend=True):
    fig.update_layout(
        template="plotly_white", height=height, font=PLOT_FONT,
        margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None) if legend else None,
        showlegend=legend,
    )
    fig.update_xaxes(showgrid=False, title=None)
    fig.update_yaxes(gridcolor="#ececec", zeroline=True, zerolinecolor="#bdbdbd", title=None,
                     ticksuffix=ysuffix, tickprefix=yprefix)
    return fig


def line(data, y, plats, ysuffix="", yprefix="", height=360, hover_fmt=",.1f"):
    d = data[data.platform.isin(plats)].dropna(subset=[y])
    fig = px.line(d, x="quarter", y=y, color="platform", markers=True,
                  color_discrete_map=COL, category_orders={"quarter": m.QUARTERS, "platform": ["Blinkit", "Zepto", "Instamart"]})
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7),
                      hovertemplate=f"%{{fullData.name}}: {yprefix}%{{y:{hover_fmt}}}{ysuffix}<extra></extra>")
    return style(fig, height, ysuffix, yprefix)


# ---------- sidebar ----------
with st.sidebar:
    st.header("Filters")
    plats = st.multiselect("Companies", ["Blinkit", "Instamart", "Zepto"], default=["Blinkit", "Instamart", "Zepto"])
    q_from, q_to = st.select_slider("Quarter range", options=m.QUARTERS, value=("Q1FY25", "Q1FY27"))
    st.divider()
    st.markdown(
        "**Reading the numbers**\n\n"
        "- **NOV**: what customers actually paid (after discounts). Blinkit & Instamart.\n"
        "- **NRV**: Zepto's version. It also includes ad income and fees, so it runs a bit high.\n"
        "- Indian fiscal year: Q1FY27 = Apr–Jun 2026.\n"
        "- ₹1 Cr = ₹10 million. ₹1 lakh = ₹100,000."
    )
    st.divider()
    st.caption("Built by Arnav · data from company filings up to Q1FY27 (Jun 2026). "
               "Zepto is unlisted, so its data stops at Mar 2026 (IPO filing).")

if not plats:
    st.warning("Pick at least one company in the sidebar.")
    st.stop()

sel = m.QUARTERS[m.QUARTERS.index(q_from): m.QUARTERS.index(q_to) + 1]
dfv = df[df.quarter.isin(sel)]

# ---------- header ----------
st.title("Quick commerce: who's actually making money?")
st.markdown(
    "Blinkit, Swiggy Instamart and Zepto all promise groceries in minutes. Only one of them is profitable. "
    "I pulled every number I could find from their shareholder letters and Zepto's IPO filing to work out **why**. "
    "Short version: it comes down to **how busy each dark store is**, and **how often customers come back**."
)

last_b, last_i, last_z = B.loc["Q1FY27"], I.loc["Q1FY27"], Z.loc["Q4FY26"]
share_now = last_b.nov_cr / (last_b.nov_cr + last_i.nov_cr) * 100
share_then = B.loc["Q1FY25"].nov_cr / (B.loc["Q1FY25"].nov_cr + I.loc["Q1FY25"].nov_cr) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Blinkit NOV, Q1FY27", f"₹{last_b.nov_cr:,.0f} Cr", f"{(last_b.nov_cr / B.loc['Q1FY26'].nov_cr - 1) * 100:.0f}% YoY")
c2.metric("Instamart NOV, Q1FY27", f"₹{last_i.nov_cr:,.0f} Cr", f"{(last_i.nov_cr / I.loc['Q1FY26'].nov_cr - 1) * 100:.0f}% YoY")
c3.metric("Blinkit share (vs Instamart)", f"{share_now:.0f}%", f"{share_now - share_then:+.0f} pts in 2 yrs")
c4.metric("Zepto orders, Q4FY26", f"{last_z.orders_mn:,.0f} M", f"{(last_z.orders_mn / Z.loc['Q4FY25'].orders_mn - 1) * 100:.0f}% YoY")

tabs = st.tabs(["Market", "Store economics", "Per-order P&L", "Customers", "Break-even simulator", "Industry & timeline", "Data & method"])

# ======================================================================
with tabs[0]:
    left, right = st.columns(2)
    with left:
        st.subheader("Orders per quarter")
        st.plotly_chart(line(dfv, "orders_mn", plats, " M"), width="stretch")
        st.caption("Blinkit only started disclosing orders in Q1FY26 (and counts cancelled orders). "
                   "Zepto's last reported quarter is Q4FY26.")
    with right:
        st.subheader("Blinkit vs Instamart, share of NOV")
        s = df[df.platform.isin(["Blinkit", "Instamart"]) & df.quarter.isin(sel)].dropna(subset=["nov_cr"])
        s = s.pivot_table(index="quarter", columns="platform", values="nov_cr", observed=True).dropna()
        s = (s.div(s.sum(axis=1), axis=0) * 100).reset_index().melt(id_vars="quarter", var_name="platform", value_name="share")
        fig = px.bar(s, x="quarter", y="share", color="platform", color_discrete_map=COL,
                     category_orders={"platform": ["Blinkit", "Instamart"]})
        fig.update_traces(hovertemplate="%{fullData.name}: %{y:.1f}%<extra></extra>", marker_line_color="white", marker_line_width=1.5)
        st.plotly_chart(style(fig, ysuffix="%").update_yaxes(range=[0, 100]), width="stretch")
        st.caption("Zepto is left out here because it reports NRV, which isn't directly comparable to NOV.")

    # three-way order share where all three report
    common = ["Q1FY26", "Q2FY26", "Q3FY26", "Q4FY26"]
    osh = df[df.quarter.isin(common)].pivot_table(index="quarter", columns="platform", values="orders_mn", observed=True)
    osh = (osh.div(osh.sum(axis=1), axis=0) * 100).round(1)
    st.markdown("#### Three-way order share (only quarters where all three disclose orders)")
    st.dataframe(osh[["Blinkit", "Zepto", "Instamart"]].style.format("{:.1f}%"), width="stretch")
    st.info(
        f"**What I take from this:** Blinkit's share of Blinkit + Instamart NOV went from {share_then:.0f}% to {share_now:.0f}% in two years. "
        f"On orders, Zepto is a clear #2 ({osh.loc['Q4FY26', 'Zepto']:.0f}% in Q4FY26) and has more than 1.8× Instamart's volume. "
        "Instamart is third on orders. Its basket (₹508) is about the same as Blinkit's and well above Zepto's (about ₹387 NRV)."
    )

# ======================================================================
with tabs[1]:
    st.markdown("Every dark store has rent, staff and a minimum number of riders to pay for, whatever it sells. "
                "So the question that matters is **how much each store sells per day**.")
    a, b = st.columns(2)
    with a:
        st.subheader("Orders per store per day")
        st.plotly_chart(line(dfv, "orders_per_store_day", plats, hover_fmt=",.0f"), width="stretch")
        st.caption("Instamart and Zepto report this directly. Blinkit's is my estimate: orders ÷ average stores ÷ 91 days.")
    with b:
        st.subheader("Sales per store per day (₹ lakh)")
        st.plotly_chart(line(dfv, "value_per_store_day_lakh", plats, "L", "₹"), width="stretch")
        st.caption("NOV for Blinkit & Instamart, NRV for Zepto. My Blinkit estimate is within ±4% of the figure Blinkit publishes.")

    zq = Z.loc["Q4FY26"]
    st.warning(
        f"**Zepto doesn't fit the simple 'busier stores = profit' story.** Its stores handled about {zq.orders_per_store_day:,.0f} orders a day in Q4FY26, "
        f"the most of the three, and did about ₹{zq.value_per_store_day_lakh:.1f} lakh a day, close to Blinkit. It still lost "
        f"{m.fmt_inr(zq.ebitda_per_order)} per order. Two reasons: a smaller basket (about ₹{zq.value_per_order:,.0f} NRV per order vs ₹518 NOV at Blinkit), "
        "and much heavier spend on marketing and delivery. Busy stores are necessary for profit. They aren't enough on their own."
    )

    c, d = st.columns(2)
    with c:
        st.subheader("Fixed cost per store per day (₹ '000)")
        st.plotly_chart(line(dfv, "fixed_per_store_day_k", [p for p in plats if p != "Zepto"], "k", "₹"), width="stretch")
        st.caption("Fixed cost = contribution − Adj. EBITDA (overheads, tech, brand marketing). Zepto doesn't disclose contribution.")
    with d:
        st.subheader("Operating leverage")
        sc = df[df.platform.isin(plats) & df.quarter.isin(sel)].dropna(subset=["value_per_store_day_lakh", "ebitda_pct"])
        fig = px.scatter(sc, x="value_per_store_day_lakh", y="ebitda_pct", color="platform", color_discrete_map=COL,
                         hover_data={"quarter": True, "value_per_store_day_lakh": ":.1f", "ebitda_pct": ":.1f", "platform": False})
        for p in sc.platform.unique():
            t = sc[sc.platform == p]
            fig.add_trace(go.Scatter(x=t.value_per_store_day_lakh, y=t.ebitda_pct, mode="lines",
                                     line=dict(color=COL[p], width=1), opacity=0.35, showlegend=False, hoverinfo="skip"))
        fig.update_traces(marker=dict(size=10, line=dict(color="white", width=1.5)), selector=dict(mode="markers"))
        fig = style(fig, ysuffix="%")
        fig.update_layout(hovermode="closest")
        fig.update_xaxes(title="Sales per store per day (₹ lakh)")
        fig.update_yaxes(title="Adj. EBITDA margin")
        st.plotly_chart(fig, width="stretch")
        st.caption("Each dot is one quarter. Up and to the right is better.")

# ======================================================================
with tabs[2]:
    st.subheader("Adj. EBITDA per order (₹)")
    st.plotly_chart(line(dfv, "ebitda_per_order", plats, yprefix="₹", hover_fmt=",.0f"), width="stretch")
    st.caption("Zepto's figure is as reported in its IPO filing. Blinkit & Instamart = Adj. EBITDA ÷ orders.")

    st.subheader("Where one order's money goes")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        who = st.radio("Company", ["Blinkit", "Instamart"], horizontal=True)
        qopts = [q for q in m.QUARTERS if q in series(who).dropna(subset=["cm_per_order"]).index]
        q_pick = st.selectbox("Quarter", qopts, index=len(qopts) - 1)
        st.caption("Zepto doesn't disclose contribution, so it can't be split this way.")
    r = series(who).loc[q_pick]
    with col_b:
        fig = go.Figure(go.Waterfall(
            orientation="v", measure=["relative", "relative", "total"],
            x=["Contribution<br>(after all variable costs)", "Fixed costs<br>(overheads, brand, tech)", "Adj. EBITDA"],
            y=[r.cm_per_order, -r.fixed_per_order, 0],
            text=[m.fmt_inr(r.cm_per_order, 1), m.fmt_inr(-r.fixed_per_order, 1), m.fmt_inr(r.ebitda_per_order, 1)],
            textposition="outside",
            increasing=dict(marker_color=COL[who]), decreasing=dict(marker_color="#c9c7c0"),
            totals=dict(marker_color="#31333F"), connector=dict(line=dict(color="#bdbdbd"))))
        fig = style(fig, 340, yprefix="₹", legend=False)
        fig.update_layout(hovermode=False)
        st.plotly_chart(fig, width="stretch")

    st.subheader("Contribution margin (% of NOV)")
    st.plotly_chart(line(dfv, "cm_pct", [p for p in plats if p != "Zepto"], "%", height=320), width="stretch")
    st.caption("Instamart reports this as % of GOV; I restated it to % of NOV so it lines up with Blinkit.")

# ======================================================================
with tabs[3]:
    st.markdown("Sales = **users × how often they order × basket size**. Splitting growth this way shows what's actually driving it.")
    a, b = st.columns(2)
    with a:
        st.subheader("Orders per user per month")
        st.plotly_chart(line(dfv, "freq_per_month", [p for p in plats if p != "Zepto"], hover_fmt=".2f"), width="stretch")
    with b:
        st.subheader("Basket size (₹ per order)")
        st.plotly_chart(line(dfv, "value_per_order", plats, yprefix="₹", hover_fmt=",.0f"), width="stretch")
        st.caption("NOV per order for Blinkit/Instamart; NRV per order for Zepto (includes ads & fees, so a bit inflated).")

    st.subheader("What drove NOV growth?")
    avail = [q for q in m.QUARTERS if q in B.dropna(subset=["mtu_mn"]).index]
    c1, c2 = st.columns(2)
    q0 = c1.selectbox("From", avail, index=0)
    q1 = c2.selectbox("To", avail, index=len(avail) - 1)
    if m.QUARTERS.index(q1) <= m.QUARTERS.index(q0):
        st.info("Pick a 'To' quarter after the 'From' quarter.")
    else:
        rows = []
        for p, d in [("Blinkit", B), ("Instamart", I)]:
            parts, total = m.growth_decomposition(d, q0, q1)
            for k, v in parts.items():
                rows.append({"platform": p, "driver": k, "pp": v})
            rows.append({"platform": p, "driver": "Total", "pp": total})
        dec = pd.DataFrame(rows)
        fig = px.bar(dec[dec.driver != "Total"], x="pp", y="platform", color="driver", orientation="h",
                     color_discrete_map={"Users": "#31333F", "Frequency": "#8a8984", "Basket": "#c9c7c0"},
                     category_orders={"driver": ["Users", "Frequency", "Basket"]})
        fig.update_traces(hovertemplate="%{fullData.name}: %{x:+.1f} pts<extra></extra>", marker_line_color="white", marker_line_width=1)
        fig = style(fig, 260, ysuffix="")
        fig.update_layout(barmode="relative", hovermode="closest")
        fig.update_xaxes(title="Percentage points of NOV growth", ticksuffix=" pts", showgrid=True, gridcolor="#ececec")
        st.plotly_chart(fig, width="stretch")
        tot = dec[dec.driver == "Total"].set_index("platform").pp
        st.caption(f"Total NOV growth {q0} → {q1}: Blinkit {tot['Blinkit']:.0f}%, Instamart {tot['Instamart']:.0f}%.")

    st.info(
        "**What I take from this:** Blinkit's growth has come almost entirely from new users; its frequency has held at about 3.5 orders a month. "
        "Instamart grew mostly through bigger baskets, while its frequency fell from about 3.6 to 2.8 as it deliberately dropped 4M+ unprofitable users. "
        "Swiggy says 1-month retention of the users it kept rose from 55% to 61%."
    )

# ======================================================================
with tabs[4]:
    st.markdown(
        "A simple model of Instamart's quarterly Adj. EBITDA: **sales × contribution margin − fixed costs**. "
        "It starts at Q1FY27 actuals. Swiggy says it breaks even at about **₹60,000 Cr of annual NOV with a 5–6% margin**. "
        "Move the levers and see how far off that is."
    )
    presets = {
        "Q1FY27 actuals": dict(mtu=13.5, freq=2.83, basket=508, cm=-0.3, fixed=0, gig=0.0),
        "Swiggy's break-even case": dict(mtu=34.0, freq=2.83, basket=520, cm=5.5, fixed=8, gig=0.0),
        "Blinkit's habits, today's users": dict(mtu=13.5, freq=3.47, basket=518, cm=5.3, fixed=0, gig=0.0),
    }
    pick = st.radio("Start from", list(presets), horizontal=True)
    p = presets[pick]
    k = pick  # separate widget keys per preset so switching resets the sliders

    s1, s2, s3 = st.columns(3)
    mtu = s1.slider("Monthly users (M)", 8.0, 45.0, p["mtu"], 0.5, key=f"mtu{k}", help="Q1FY27: 13.5M. Blinkit: 31.8M.")
    freq = s2.slider("Orders per user per month", 2.0, 4.5, p["freq"], 0.01, key=f"freq{k}", help="Q1FY27: 2.83. Blinkit: 3.47.")
    basket = s3.slider("Basket size (₹ NOV per order)", 400, 700, p["basket"], 5, key=f"bsk{k}", help="Q1FY27: ₹508. Blinkit: ₹518.")
    s4, s5, s6 = st.columns(3)
    cm = s4.slider("Contribution margin (% of NOV)", -3.0, 8.0, p["cm"], 0.1, key=f"cm{k}", help="Q1FY27: about −0.3%. Blinkit: 5.3%.")
    fixed_g = s5.slider("Fixed costs vs today (+%)", 0, 50, p["fixed"], 1, key=f"fx{k}", help="Q1FY27 fixed costs ≈ ₹762 Cr a quarter.")
    gig = s6.slider("Gig-worker social security cost (₹/order)", 0.0, 5.0, p["gig"], 0.25, key=f"gig{k}",
                    help="New labour codes: platforms pay 1–2% of turnover, capped at 5% of what they pay delivery partners. "
                         "I don't know the exact per-order figure, so it's a slider.")

    fixed_now = float(I.loc["Q1FY27"].fixed_cr)
    out = m.instamart_ebitda(mtu, freq, basket, cm, fixed_now * (1 + fixed_g / 100), gig)
    be_nov = (fixed_now * (1 + fixed_g / 100)) / (cm / 100) * 4 if cm > 0 else None

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Quarterly Adj. EBITDA", m.fmt_inr(out["ebitda_cr"], 0, " Cr"),
              f"{out['ebitda_cr'] - float(I.loc['Q1FY27'].adj_ebitda_cr):+,.0f} Cr vs Q1FY27")
    o2.metric("Annual NOV run-rate", f"₹{out['annual_nov_cr']:,.0f} Cr")
    o3.metric("EBITDA per order", m.fmt_inr(out["ebitda_per_order"], 1))
    o4.metric("Break-even NOV at this margin", f"₹{be_nov:,.0f} Cr" if be_nov else "Never",
              help="Annual NOV needed to cover fixed costs. Needs a positive contribution margin.")

    if out["ebitda_cr"] >= 0:
        st.success(f"Profitable at the EBITDA level. That needs about {out['orders_mn']:,.0f}M orders a quarter (Q1FY27: 114M).")
    else:
        st.error(f"Still loss-making. Orders per quarter in this scenario: {out['orders_mn']:,.0f}M (Q1FY27: 114M).")

    with st.expander("Heatmap: EBITDA by margin and scale"):
        cm_grid = np.round(np.arange(-1, 7.5, 0.5), 1)
        nov_grid = np.arange(20_000, 90_000, 5_000)
        fx = fixed_now * (1 + fixed_g / 100)
        zz = np.array([[n / 4 * c / 100 - fx for n in nov_grid] for c in cm_grid])
        lim = np.abs(zz).max()
        fig = go.Figure(go.Heatmap(
            z=zz, x=[f"{n // 1000}k" for n in nov_grid], y=[f"{c:.1f}%" for c in cm_grid],
            colorscale=[[0, "#c0392b"], [0.5, "#f5f5f2"], [1, COL["Blinkit"]]], zmin=-lim, zmax=lim,
            hovertemplate="Annual NOV ₹%{x} Cr<br>Margin %{y}<br>EBITDA ₹%{z:,.0f} Cr / qtr<extra></extra>",
            colorbar=dict(title="₹ Cr/qtr")))
        fig = style(fig, 420, legend=False)
        fig.update_xaxes(title="Annual NOV (₹ Cr)")
        fig.update_yaxes(title="Contribution margin", zeroline=False)
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Uses fixed costs of ₹{fx:,.0f} Cr a quarter (your setting above). Blue = profit, red = loss.")

    st.markdown(
        "**What this tells me:** getting the margin to 5.5% isn't enough on its own. At today's size that's still a loss of about ₹440 Cr a quarter. "
        "Instamart has to get roughly **2.5× bigger** (₹55–64k Cr annual NOV, depending on how fixed costs grow). "
        "Raising frequency is the cheapest route there: at Blinkit's 3.47 orders a month it would need about 6M fewer users to reach the same size."
    )

# ======================================================================
with tabs[5]:
    st.subheader("The race is getting crowded")
    ctx = context[context.metric == "dark_stores"].sort_values("as_of").groupby("player").tail(1)
    ctx = ctx.sort_values("value")
    ctx["color"] = ctx.player.map(lambda x: COL.get(x, COL["Other"]))
    fig = go.Figure(go.Bar(x=ctx.value, y=ctx.player, orientation="h", marker_color=ctx.color,
                           text=[f"{v:,.0f}  ({d:%b %Y})" for v, d in zip(ctx.value, ctx.as_of)], textposition="outside",
                           hovertemplate="%{y}: %{x:,.0f} stores<extra></extra>"))
    fig = style(fig, 320, legend=False)
    fig.update_xaxes(range=[0, ctx.value.max() * 1.3], title="Dark stores (latest figure I could find)")
    fig.update_layout(hovermode="closest")
    st.plotly_chart(fig, width="stretch")
    st.caption("Blinkit, Instamart and Zepto from filings. Flipkart Minutes and Amazon Now are Bernstein estimates or company statements "
               "(reported by Business Standard), so treat them as approximate. Redseer puts the whole market at about ₹11,000 Cr GMV a month "
               "(Jan 2026), roughly doubling year on year.")

    st.subheader("Timeline")
    for _, e in events.sort_values("date", ascending=False).iterrows():
        tag = e.player if e.player in COL else "Industry"
        st.markdown(f"**{e.date:%d %b %Y}** · *{tag}* · {e.event} ([source]({e.source}))")

    st.subheader("What the market thinks it's worth")
    v = vals.copy()
    v["as of"] = v.as_of.dt.strftime("%b %Y")
    v["value"] = np.where(v.metric == "market_cap_cr", v.value.map(lambda x: f"₹{x:,.0f} Cr"), v.value.map(lambda x: f"${x:.2f} bn"))
    st.dataframe(v[["company", "value", "as of", "basis"]], hide_index=True, width="stretch")
    st.caption("Eternal and Swiggy market caps include their food delivery businesses, so they're not pure quick-commerce valuations. "
               "Zepto's July 2026 figure is an implied price from unlisted-share trading, not a funding round.")

# ======================================================================
with tabs[6]:
    st.subheader("How I built this")
    st.markdown(
        "- **Sources:** Eternal (Blinkit) and Swiggy (Instamart) quarterly shareholder letters; Zepto's updated DRHP filed with SEBI in June 2026. "
        "Every row in the CSVs has its source link.\n"
        "- **Derived numbers:** some Instamart GOV/NOV figures are orders × AOV × NOV%, and Blinkit's orders per store per day is my estimate. "
        "These are flagged in the `notes` column.\n"
        "- **Checks:** my Blinkit NOV per store per day matches the published figure within ±4%. Zepto's FY26 order count and EBITDA from the "
        "quarterly table add up exactly to the annual numbers reported in the press.\n"
        "- **Caveats:** Blinkit counts cancelled orders; Zepto reports NRV (includes ads and fees) rather than NOV; "
        "'fixed cost' (contribution − EBITDA) lumps brand marketing in with overheads."
    )
    show = st.selectbox("Table", ["Blinkit & Instamart (quarterly)", "Zepto (quarterly)", "Management guidance", "Industry context", "Events"])
    tbl = {"Blinkit & Instamart (quarterly)": panel, "Zepto (quarterly)": zepto_q, "Management guidance": guide,
           "Industry context": context, "Events": events}[show]
    shown = tbl.copy()
    for c in shown.columns:
        if pd.api.types.is_datetime64_any_dtype(shown[c]):
            shown[c] = shown[c].dt.strftime("%d %b %Y")
    st.dataframe(shown, hide_index=True, width="stretch",
                 column_config={"source": st.column_config.LinkColumn("source", display_text="link")})
    st.download_button("Download this table (CSV)", tbl.to_csv(index=False).encode(), file_name=f"{show.split(' ')[0].lower()}.csv", mime="text/csv")
    st.caption("Not affiliated with any of these companies. Nothing here is investment advice.")
