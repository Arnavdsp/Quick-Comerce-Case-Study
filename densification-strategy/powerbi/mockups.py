"""
Page layouts for the Power BI dashboard. One source for both the wireframe
images (mockups/) and the per-page tables in BUILD_GUIDE.md.

    python mockups.py

Positions are in pixels on Power BI's default 1280 x 720 canvas; type them into
Format > General > Properties > Size and position.
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

import sys  # noqa: E402
from math import exp, pi, sqrt  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import model  # noqa: E402

OUT = HERE / "mockups"
DATA = HERE / "data"
ORANGE, BLUE, GREY, INK2 = "#EB6834", "#2A78D6", "#A3A29C", "#55544F"
GUIDE = HERE / "BUILD_GUIDE.md"

KIND = {  # fill, edge, label colour
    "card": ("#FDF0EA", "#EB6834", "#1D1D1B"),
    "chart": ("#FFFFFF", "#A3A29C", "#1D1D1B"),
    "slicer": ("#FFF7F2", "#EB6834", "#1D1D1B"),
    "table": ("#FFFFFF", "#55544F", "#1D1D1B"),
    "text": ("#F3F3F1", "#F3F3F1", "#1D1D1B"),
}

# name, visual, kind, (x, y, w, h), fields / settings
PAGES = [
    ("1 Market", "Same basket, emptier stores", [
        ("Page title", "Text box", "text", (20, 14, 900, 46), "Same basket, emptier stores. Segoe UI Semibold 22"),
        ("Quarter range", "Slicer (Between)", "slicer", (1000, 14, 260, 50), "dim_quarter[SortOrder] as a range; label it 'Quarter'"),
        ("Instamart ₹/store/day", "Card", "card", (20, 76, 236, 110), "[Instamart NOV per Store-Day L]"),
        ("Blinkit ₹/store/day", "Card", "card", (271, 76, 236, 110), "[Blinkit NOV per Store-Day L]"),
        ("Throughput gap", "Card", "card", (522, 76, 236, 110), "[Throughput Gap %]  (31%)"),
        ("Blinkit share of NOV", "Card", "card", (773, 76, 236, 110), "[Blinkit Share of NOV]; visual filter Quarter = Q1FY27  (75%)"),
        ("Instamart utilisation", "Card", "card", (1024, 76, 236, 110), "[Utilisation Today]  (40%)"),
        ("NOV per store per day", "Line chart", "chart", (20, 202, 780, 500),
         "X dim_quarter[Quarter] (sorted by SortOrder), Y [NOV per Store-Day L], Legend dim_platform[Platform]. "
         "Analytics: constant line at 11, label 'Blinkit steady-state target'"),
        ("Net basket, Q1FY27", "Clustered column", "chart", (815, 202, 445, 240),
         "X dim_platform[Platform], Y [Net AOV]; visual filter Quarter = Q1FY27; data labels on"),
        ("HQ cost per store-day, Q1FY27", "Clustered column", "chart", (815, 457, 445, 245),
         "X dim_platform[Platform], Y [HQ Cost per Store-Day k]; visual filter Quarter = Q1FY27; data labels on"),
    ]),
    ("2 Root cause", "Three-quarters of the gap is volume, and volume is frequency", [
        ("Page title", "Text box", "text", (20, 14, 1240, 46), "Three-quarters of the gap is volume, and volume is frequency"),
        ("Per-order EBITDA gap, Q1FY27", "Waterfall", "chart", (20, 76, 620, 380),
         "Category per_order_gap[Step] (sort by SortOrder), Y Sum of Rs_per_Order. Rename the total bar 'Instamart' in "
         "Format > X-axis if your version allows; otherwise add a text box. Decrease colour #C9442F"),
        ("Users per store", "Clustered column", "chart", (655, 76, 195, 380),
         "X throughput[Platform], Y Sum of Value; visual filter Metric = 'Users per store'"),
        ("Orders per user per month", "Clustered column", "chart", (860, 76, 195, 380),
         "Same, Metric = 'Orders per user per month'"),
        ("Orders per store per day", "Clustered column", "chart", (1065, 76, 195, 380),
         "Same, Metric = 'Orders per store per day'"),
        ("Order frequency over time", "Line chart", "chart", (20, 472, 620, 230),
         "X dim_quarter[Quarter], Y [Order Frequency], Legend dim_platform[Platform]; filter Quarter >= Q1FY26"),
        ("Five whys", "Table", "table", (655, 472, 605, 230), "five_whys[Step], [Question], [Answer]; word wrap on"),
    ]),
    ("3 Simulator", "Break-even simulator", [
        ("Dynamic headline", "Card (new) or multi-row card", "text", (20, 14, 1240, 50), "[Simulator Headline], left aligned, 16pt"),
        ("Plan delivery %", "Slicer (Single value)", "slicer", (20, 76, 280, 110), "'Plan Delivery'[Plan Delivery]"),
        ("Store rent + staff ₹/day", "Slicer (Single value)", "slicer", (20, 196, 280, 110), "'Store Cost'[Store Cost]"),
        ("Per-order levers ₹", "Slicer (Single value)", "slicer", (20, 316, 280, 110), "'Per Order Levers'[Per Order Levers]"),
        ("Programme spend ₹/order", "Slicer (Single value)", "slicer", (20, 436, 280, 110), "'Programme Spend'[Programme Spend]"),
        ("Plays switched on", "Slicer (Vertical list)", "slicer", (20, 556, 280, 146),
         "plays[Play]; visual filter InPlan = True; Select all on"),
        ("CM before", "Card", "card", (315, 76, 147, 110), "[CM % Before]"),
        ("CM after", "Card", "card", (474, 76, 147, 110), "[CM % After]"),
        ("Stores in the black, before", "Card", "card", (633, 76, 147, 110), "[Stores CM Positive Before]"),
        ("Stores in the black, after", "Card", "card", (792, 76, 147, 110), "[Stores CM Positive After]"),
        ("Net contribution ₹ Cr/yr", "Card", "card", (951, 76, 147, 110), "[Annual Net Contribution Cr]"),
        ("Stores avoided", "Card", "card", (1110, 76, 150, 110), "[Stores Avoided]"),
        ("Profit per store-day at each throughput", "Line chart", "chart", (315, 200, 465, 502),
         "X 'NOV Grid'[NOV_Lakh] (continuous; filter 4.5 to 12.5), Y [Contribution per Store-Day k], "
         "[EBITDA per Store-Day Today k], [EBITDA per Store-Day With Levers k]. Analytics: Y constant line 0; "
         "X constant lines at [Base NOV Day L] and [New NOV Day L] via fx"),
        ("Stores by daily sales", "Area chart", "chart", (795, 200, 465, 502),
         "X 'NOV Grid'[NOV_Lakh] (continuous; filter 0.5 to 12.5), Y [Store Density Today] (grey, no fill), "
         "[Store Density After] (orange line), [Store Density After Above BE] (orange fill). "
         "X constant line at [Store Breakeven NOV L] via fx"),
    ]),
    ("4 The plan", "Four plays, about ₹1 lakh per store per day", [
        ("Page title", "Text box", "text", (20, 14, 1240, 46), "Four plays, about ₹1 lakh per store per day"),
        ("Candidate plays", "Scatter chart", "chart", (20, 76, 620, 380),
         "Values plays[Play], X plays[Ease], Y plays[Impact_k], Legend plays[Status]; category labels on; "
         "colours: In the plan #EB6834, Parked #A3A29C, Rejected #55544F"),
        ("Where the ₹1 lakh comes from", "Waterfall", "chart", (655, 76, 605, 380),
         "Category lever_stack[Step] (sort by SortOrder), Y Sum of NOV_k; total bar = after plan; Y axis starts at 450"),
        ("The four plays", "Table", "table", (20, 472, 1240, 230),
         "plays[Play], [Impact_k], [OrdersAdded_Day], [What], [Target]; visual filter InPlan = True; word wrap on"),
    ]),
    ("5 Scorecard", "Measure the habit, not just the orders", [
        ("Page title", "Text box", "text", (20, 14, 1240, 46), "Measure the habit, not just the orders"),
        ("North star today", "Card", "card", (20, 76, 300, 90), "[Base NOV Day L], label 'NOV per store per day, Q1FY27'"),
        ("North star target", "Card", "card", (20, 178, 300, 90), "[New NOV Day L], label 'Target after the plan'"),
        ("Stores avoided", "Card", "card", (20, 280, 300, 90), "[Stores Avoided], label 'Fewer stores to reach ₹60k Cr'"),
        ("Capex avoided", "Card", "card", (20, 382, 300, 94), "[Capex Avoided Cr], label '₹ Cr of capex not spent'"),
        ("HEART scorecard", "Table", "table", (335, 76, 925, 400),
         "heart[Dimension], [Goal], [Signal], [Metric], [Baseline], [Target]; sort by SortOrder; "
         "conditional background on Dimension: Guardrail = #FDF0EA"),
        ("Q2FY27: what moved contribution", "Waterfall", "chart", (20, 490, 620, 212),
         "Category q2fy27_cm_bridge[Step] (sort by SortOrder), Y Sum of bps; total bar = Q2FY27 (−100 bps)"),
        ("What happened next", "Text box", "text", (655, 490, 605, 212),
         "Orders per store rose 9.5% in Q2FY27 and Swiggy credits that with +60 bps. Pricing (−100) and mix (−40) "
         "gave it back. Density works; buy the habit with product, not price."),
    ]),
]


# ---- what each visual should look like with the default slider values ----
_, I, B, _ = model.baseline()
P = model.plan(I)
S = P["store"]
T = {f.stem: pd.read_csv(f) for f in DATA.glob("*.csv")}
VM2 = model.with_levers(S, 24.5)
CARD = {
    "[Instamart NOV per Store-Day L]": f"₹{I.value_per_store_day_lakh:.2f}L",
    "[Blinkit NOV per Store-Day L]": f"₹{B.value_per_store_day_lakh:.2f}L",
    "[Throughput Gap %]": f"{1 - I.value_per_store_day_lakh / B.value_per_store_day_lakh:.0%}",
    "[Blinkit Share of NOV]": f"{B.nov_cr / (B.nov_cr + I.nov_cr):.0%}",
    "[Utilisation Today]": "40%",
    "[CM % Before]": f"{P['cm_pct_before']:+.1f}%".replace("-", "−"),
    "[CM % After]": f"{P['cm_pct_after']:+.1f}%",
    "[Stores CM Positive Before]": f"{P['share_cm_positive_before']:.0%}",
    "[Stores CM Positive After]": f"{P['share_cm_positive_after']:.0%}",
    "[Annual Net Contribution Cr]": f"₹{P['annual_net_cr']:,.0f} Cr",
    "[Stores Avoided]": f"{P['stores_avoided']:,.0f}",
    "[Base NOV Day L]": f"₹{S['nov']/1e5:.2f}L",
    "[New NOV Day L]": f"₹{P['new_nov']/1e5:.2f}L",
    "[Capex Avoided Cr]": f"₹{P['capex_avoided_cr']:,.0f} Cr",
}


plt.rcParams["font.family"] = "Carlito"


def _style(ax):
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(labelsize=8, colors=INK2, length=0)
    ax.grid(axis="y", color="#E6E5E1", lw=0.6)
    ax.set_axisbelow(True)


def _waterfall(ax, labels, vals, total_label, cols):
    run = 0
    for k, v in enumerate(vals):
        ax.bar(k, v, bottom=run if k else 0, color=cols[k], width=0.6)
        run = v if k == 0 else run + v
    ax.bar(len(vals), run, color=ORANGE, width=0.6)
    ax.set_xticks(range(len(vals) + 1))
    ax.set_xticklabels(labels + [total_label], fontsize=7)


def pv_nov_line(ax):
    q = T["dim_quarter"].Quarter.tolist()
    f = T["fact_quarterly"]
    for plat, col in [("Blinkit", BLUE), ("Instamart", ORANGE)]:
        d = f[f.Platform == plat].set_index("Quarter").reindex(q)
        ax.plot(q, d.NOV_Cr * 100 / d.StoreDays, color=col, marker="o", ms=3, lw=2, label=plat)
    ax.axhline(11, color=BLUE, ls="--", lw=1)
    ax.set_ylim(0, 12)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    ax.tick_params(axis="x", labelsize=7)


def _two_bars(ax, iv, bv, fmt):
    ax.bar([0, 1], [iv, bv], color=[ORANGE, BLUE], width=0.55)
    for x, v in [(0, iv), (1, bv)]:
        ax.text(x, v, fmt.format(v), ha="center", va="bottom", fontsize=8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Instamart", "Blinkit"], fontsize=8)
    ax.set_yticks([])


def pv_aov(ax):
    _two_bars(ax, I.value_per_order, B.value_per_order, "₹{:.0f}")


def pv_hq(ax):
    _two_bars(ax, I.fixed_per_store_day_k, B.fixed_per_store_day_k, "₹{:.0f}k")


def pv_gap(ax):
    g = T["per_order_gap"].sort_values("SortOrder")
    _waterfall(ax, ["Blinkit", "HQ costs", "Store costs", "Ads, 1P"], g.Rs_per_Order.tolist(), "Instamart",
               [BLUE, "#C9442F", "#C9442F", GREY])
    ax.axhline(0, color=INK2, lw=0.6)


def _metric(name, fmt):
    def f(ax):
        d = T["throughput"][T["throughput"].Metric == name].set_index("Platform").Value
        _two_bars(ax, d["Instamart"], d["Blinkit"], fmt)
    return f


def pv_freq(ax):
    q = ["Q1FY26", "Q2FY26", "Q3FY26", "Q4FY26", "Q1FY27"]
    f = T["fact_quarterly"]
    for plat, col in [("Blinkit", BLUE), ("Instamart", ORANGE)]:
        d = f[f.Platform == plat].set_index("Quarter").reindex(q)
        ax.plot(q, d.Orders_Mn / d.UserMonths_Mn, color=col, marker="o", ms=3, lw=2)
    ax.set_ylim(2, 4)


def pv_floors(ax):
    x = np.linspace(4.5, 12.5, 50)
    ax.plot(x, (x * 1e5 * S["var_margin"] - S["semi_fixed"]) / 1e3, color=ORANGE, lw=2)
    ax.plot(x, (x * 1e5 * S["var_margin"] - S["semi_fixed"] - S["fixed"]) / 1e3, color=ORANGE, lw=1.5, ls=":")
    ax.plot(x, (x * 1e5 * VM2 - S["semi_fixed"] - S["fixed"]) / 1e3, color="#1D1D1B", lw=2)
    ax.axhline(0, color=INK2, lw=0.8)
    for v in (S["nov"] / 1e5, P["new_nov"] / 1e5):
        ax.axvline(v, color=GREY, ls="--", lw=0.8)


def pv_density(ax):
    x = np.linspace(0.5, 12.5, 200)
    sd = model.ASSUMPTIONS["store_nov_sd_lakh"]
    be = S["breakeven_nov_contribution"] / 1e5
    pdf = lambda mu: np.exp(-((x - mu) ** 2) / (2 * sd ** 2)) / (sd * sqrt(2 * pi))  # noqa: E731
    ax.plot(x, pdf(S["nov"] / 1e5), color=GREY, lw=2)
    after = pdf(P["new_nov"] / 1e5)
    ax.plot(x, after, color=ORANGE, lw=2)
    ax.fill_between(x, after, where=x >= be, color=ORANGE, alpha=0.3, lw=0)
    ax.axvline(be, color="#1D1D1B", lw=1)
    ax.set_yticks([])


def pv_scatter(ax):
    d = T["plays"]
    cols = {"In the plan": ORANGE, "Parked": GREY, "Rejected": INK2}
    for _, r in d.iterrows():
        ax.scatter(r.Ease, r.Impact_k, s=70 if r.InPlan else 40, color=cols[r.Status], edgecolor="white", zorder=3)
    ax.set_xlim(0.5, 5.3)


def pv_stack(ax):
    d = T["lever_stack"].sort_values("SortOrder")
    _waterfall(ax, ["Today", "Morning", "Bridge", "Win back", "Basket"], d.NOV_k.tolist(), "After",
               [GREY] + [ORANGE] * 4)
    ax.set_ylim(450, 690)


def pv_q2(ax):
    d = T["q2fy27_cm_bridge"].sort_values("SortOrder")
    _waterfall(ax, ["Q1FY27", "Pricing", "Mix", "Fuller stores"], d.bps.tolist(), "Q2FY27",
               [GREY, "#C9442F", "#C9442F", "#2F8F5B"])
    ax.axhline(0, color=INK2, lw=0.6)


def pv_table(cols, rows):
    def f(ax):
        ax.axis("off")
        n = len(rows) + 1
        for j, c in enumerate(cols):
            ax.text(j / len(cols), 1 - 0.5 / n, c, fontsize=8, fontweight="bold", color="#1D1D1B", va="center",
                    transform=ax.transAxes)
        for k, r in enumerate(rows, start=1):
            if k % 2 == 0:
                ax.add_patch(plt.Rectangle((0, 1 - (k + 1) / n), 1, 1 / n, transform=ax.transAxes, color="#F3F3F1", lw=0))
            for j, v in enumerate(r):
                v = str(v)
                ax.text(j / len(cols), 1 - (k + 0.5) / n, v if len(v) < 34 else v[:32] + "…", fontsize=7.5,
                        color=INK2, va="center", transform=ax.transAxes)
    return f


PREVIEW = {
    "NOV per store per day": pv_nov_line, "Net basket, Q1FY27": pv_aov, "HQ cost per store-day, Q1FY27": pv_hq,
    "Per-order EBITDA gap, Q1FY27": pv_gap, "Users per store": _metric("Users per store", "{:,.0f}"),
    "Orders per user per month": _metric("Orders per user per month", "{:.2f}"),
    "Orders per store per day": _metric("Orders per store per day", "{:,.0f}"),
    "Order frequency over time": pv_freq, "Profit per store-day at each throughput": pv_floors,
    "Stores by daily sales": pv_density, "Candidate plays": pv_scatter, "Where the ₹1 lakh comes from": pv_stack,
    "Q2FY27: what moved contribution": pv_q2,
}


def draw(page, title, visuals):
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1280)
    ax.set_ylim(720, 0)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1280, 720, color="#F3F3F1"))
    for name, visual, kind, (x, y, w, h), fields in visuals:
        fill, edge, col = KIND[kind]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                    fc=fill, ec=edge, lw=1.4, ls="-" if kind != "text" else ":"))
        if kind == "text":
            shown = fields.split(".")[0] if name == "Page title" else f"{name}: {fields}"
            if name == "Dynamic headline":
                shown = (f"₹{P['add_nov']/1e5:.2f}L more per store per day takes contribution from "
                         f"{P['cm_pct_before']:+.1f}% to {P['cm_pct_after']:+.1f}% and stores in the black from "
                         f"{P['share_cm_positive_before']:.0%} to {P['share_cm_positive_after']:.0%}").replace("-", "−")
            elif name == "What happened next":
                import textwrap
                shown = textwrap.fill(fields, width=int(w / 6.2))
            ax.text(x + 10, y + h / 2, shown,
                    va="center", fontsize=15 if name in ("Page title", "Dynamic headline") else 10,
                    fontweight="bold" if name in ("Page title", "Dynamic headline") else "normal",
                    color=col, family="Carlito", wrap=True)
            continue
        label = name if len(name) * 6.5 < w - 16 else name[: int((w - 16) / 6.5) - 1] + "…"
        ax.text(x + 10, y + 17, label, fontsize=11, fontweight="bold", color=col, family="Carlito", va="center")
        if kind == "card":
            val = next((v for k_, v in CARD.items() if fields.startswith(k_)), "")
            ax.text(x + 10, y + h * 0.62, val, fontsize=24 if w > 200 else 19, fontweight="bold", color=ORANGE,
                    family="Carlito", va="center")
            ax.text(x + 10, y + h - 12, visual, fontsize=8.5, color=INK2, family="Carlito", va="center", style="italic")
        elif kind == "slicer":
            ax.text(x + 10, y + 38, visual, fontsize=9, color=ORANGE, family="Carlito", va="center", style="italic")
            if "Single value" in visual:
                ax.plot([x + 12, x + w - 12], [y + 72, y + 72], color=GREY, lw=3, solid_capstyle="round")
                ax.plot([x + 12, x + w * 0.55], [y + 72, y + 72], color=ORANGE, lw=3, solid_capstyle="round")
                ax.scatter([x + w * 0.55], [y + 72], s=60, color=ORANGE, zorder=3)
            elif "list" in visual:
                for k_, pl in enumerate(T["plays"][T["plays"].InPlan].Play):
                    ax.text(x + 14, y + 62 + k_ * 20, f"☑  {pl}", fontsize=9, color="#1D1D1B", family="DejaVu Sans", va="center")
        else:
            if w < 300:
                pass
            else:
                ax.text(x + w - 10, y + 17, visual, fontsize=9, color=ORANGE, family="Carlito", va="center",
                        style="italic", ha="right")
            fx = PREVIEW.get(name)
            if name == "Five whys":
                fx = pv_table(["#", "Question", "Answer"], T["five_whys"][["Step", "Question", "Answer"]].values.tolist())
            elif name == "The four plays":
                d = T["plays"][T["plays"].InPlan]
                fx = pv_table(["Play", "₹k/day", "Orders/day", "What", "Target"],
                              d[["Play", "Impact_k", "OrdersAdded_Day", "What", "Target"]].round(0).values.tolist())
            elif name == "HEART scorecard":
                fx = pv_table(["Dimension", "Goal", "Metric", "Baseline", "Target"],
                              T["heart"][["Dimension", "Goal", "Metric", "Baseline", "Target"]].fillna("").values.tolist())
            if fx:
                sub = fig.add_axes([(x + 14) / 1280, 1 - (y + h - 10) / 720, (w - 28) / 1280, (h - 48) / 720])
                _style(sub)
                fx(sub)
    fig.savefig(OUT / f"page_{page.split()[0]}.png", metadata={"Software": None})
    plt.close(fig)


def guide_section():
    lines = []
    for page, title, visuals in PAGES:
        n = page.split()[0]
        lines += [f"### Page {page}", "", f"![Page {n} layout](mockups/page_{n}.png)", "",
                  "| Visual | Type | x, y, w, h | Fields and settings |", "|---|---|---|---|"]
        for name, visual, _, (x, y, w, h), fields in visuals:
            lines.append(f"| {name} | {visual} | {x}, {y}, {w}, {h} | {fields} |")
        lines.append("")
    return "\n".join(lines)


def checks_section():
    rows = [
        ("1 Market", "Instamart / Blinkit NOV per store-day", CARD["[Instamart NOV per Store-Day L]"] + " / " + CARD["[Blinkit NOV per Store-Day L]"]),
        ("1 Market", "Throughput gap; Blinkit share of NOV (Q1FY27)", CARD["[Throughput Gap %]"] + "; " + CARD["[Blinkit Share of NOV]"]),
        ("1 Market", "Net AOV Instamart / Blinkit (Q1FY27)", f"₹{I.value_per_order:.0f} / ₹{B.value_per_order:.0f}"),
        ("1 Market", "HQ cost per store-day Instamart / Blinkit", f"₹{I.fixed_per_store_day_k:.0f}k / ₹{B.fixed_per_store_day_k:.0f}k"),
        ("2 Root cause", "Order frequency Instamart / Blinkit (Q1FY27)", f"{I.freq_per_month:.2f} / {B.freq_per_month:.2f}"),
        ("2 Root cause", "Waterfall total (Instamart EBITDA per order)", f"−₹{-I.ebitda_per_order:.0f}"),
        ("3 Simulator", "Variable Margin", f"{S['var_margin']:.1%}"),
        ("3 Simulator", "CM before → after", CARD["[CM % Before]"] + " → " + CARD["[CM % After]"]),
        ("3 Simulator", "Stores in the black before → after", CARD["[Stores CM Positive Before]"] + " → " + CARD["[Stores CM Positive After]"]),
        ("3 Simulator", "Store Breakeven NOV L", f"₹{S['breakeven_nov_contribution']/1e5:.2f}L"),
        ("3 Simulator", "EBITDA Breakeven NOV L", f"₹{(S['semi_fixed'] + S['fixed']) / VM2 / 1e5:.1f}L"),
        ("3 Simulator", "Annual Added NOV Cr; Annual Net Contribution Cr", f"₹{P['annual_nov_cr']:,.0f} Cr; ₹{P['annual_net_cr']:,.0f} Cr"),
        ("3 Simulator", "Stores Avoided; Capex Avoided Cr", f"{P['stores_avoided']:,.0f}; ₹{P['capex_avoided_cr']:,.0f} Cr"),
        ("3 Simulator", "Utilisation After", f"{P['utilisation_after']:.0f}%"),
        ("5 Scorecard", "North star today → target", CARD["[Base NOV Day L]"] + " → " + CARD["[New NOV Day L]"]),
    ]
    out = ["| Page | Measure | Should show |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return "\n".join(out)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for p in PAGES:
        draw(*p)
        print("drew", p[0])
    if GUIDE.exists():
        g = GUIDE.read_text()
        g = re.sub(r"(<!-- pages:start -->).*?(<!-- pages:end -->)", lambda m: m.group(1) + "\n" + guide_section() + "\n" + m.group(2),
                   g, flags=re.S)
        g = re.sub(r"(<!-- checks:start -->).*?(<!-- checks:end -->)", lambda m: m.group(1) + "\n" + checks_section() + "\n" + m.group(2),
                   g, flags=re.S)
        GUIDE.write_text(g)
        print("updated BUILD_GUIDE.md")
