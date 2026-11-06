"""Draws every chart used in the deck and the write-up. Run: python charts.py"""
from math import exp, pi, sqrt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import model  # noqa: E402

OUT = Path(__file__).resolve().parent / "charts"
OUT.mkdir(exist_ok=True)

BLINKIT, INSTAMART, ZEPTO = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURF = "#1d1d1b", "#55544f", "#a3a29c", "#e6e5e1", "#ffffff"
LOSS, GAIN = "#c9442f", "#2f8f5b"

plt.rcParams.update({
    "font.family": "Carlito", "font.size": 12,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.titlecolor": INK, "legend.frameon": False, "lines.linewidth": 2.2,
    "axes.axisbelow": True, "xtick.major.size": 0, "ytick.major.size": 0,
})

df, I, B, G = model.baseline()
P = model.plan(I)
S = P["store"]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def rs(v, _=None, unit=""):
    return f"{'−' if v < 0 else ''}₹{abs(v):,.0f}{unit}"


def lakh(v, _=None):
    return f"₹{v:.0f}L" if float(v).is_integer() else f"₹{v:.1f}L"


# 1. Same basket, emptier stores ------------------------------------------------
def throughput():
    q = ["Q1FY25", "Q2FY25", "Q3FY25", "Q4FY25", "Q1FY26", "Q2FY26", "Q3FY26", "Q4FY26", "Q1FY27"]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    for name, col in [("Blinkit", BLINKIT), ("Instamart", INSTAMART)]:
        s = df[df.platform == name].set_index("quarter").value_per_store_day_lakh.reindex(q)
        ax.plot(q, s.values, color=col, marker="o", ms=7, mec=SURF, mew=2)
        ax.annotate(f"{name}  ₹{s.iloc[-1]:.1f}L", (len(q) - 1, s.iloc[-1]), xytext=(10, 0),
                    textcoords="offset points", va="center", color=INK, fontsize=12, fontweight="bold")
    ax.axhline(11, color=BLINKIT, lw=1.2, ls=(0, (4, 3)))
    ax.text(0, 11.25, "Blinkit's own steady-state target: ₹11L", color=INK2, fontsize=10.5)
    ax.set_ylim(0, 12.5)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lakh))
    ax.set_xlim(-0.3, len(q) + 1.4)
    ax.set_title("NOV per dark store per day")
    ax.tick_params(axis="x", labelsize=10.5)
    save(fig, "01_throughput")


# 2. Where the ₹71/order gap comes from -------------------------------------------
def per_order_gap():
    g = model.per_order_gap(I, B)
    steps = [("Blinkit", g["Blinkit"]), ("HQ & tech costs\nover fewer orders", g["HQ costs over fewer orders"]),
             ("Store rent & staff\nover fewer orders", g["Store costs over fewer orders"]),
             ("Ads, 1P margin,\npricing", g["Variable margin (ads, 1P, pricing)"]), ("Instamart", g["Instamart"])]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    run = 0
    for k, (lab, v) in enumerate(steps):
        if k in (0, len(steps) - 1):
            col = BLINKIT if k == 0 else INSTAMART
            ax.bar(k, v, color=col, width=0.6)
            ax.text(k, v + (3 if v >= 0 else -3), f"{'+' if v > 0 else '−'}₹{abs(v):.0f}",
                    ha="center", va="bottom" if v >= 0 else "top", fontweight="bold", color=INK)
            run = v
        else:
            vol = k in (1, 2)
            ax.bar(k, v, bottom=run, color=LOSS if vol else MUTED, width=0.6)
            ax.text(k, run + v - 3, f"−₹{abs(v):.0f}", ha="center", va="top", color=INK, fontweight="bold")
            ax.plot([k - 1 + 0.3, k - 0.3], [run, run], color=INK2, lw=0.8)
            run += v
    ax.plot([len(steps) - 2 + 0.3, len(steps) - 1 - 0.3], [run, run], color=INK2, lw=0.8)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s[0] for s in steps], fontsize=11)
    ax.set_ylim(-85, 18)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(rs))
    ax.set_title("Adj. EBITDA per order, Q1FY27 (₹)")
    ax.text(1.5, 12, f"Red = volume problems: {g['_volume_share']:.0%} of the gap", ha="center",
            color=LOSS, fontsize=11.5, fontweight="bold")
    save(fig, "02_per_order_gap")


# 3. Throughput gap = frequency + users per store ---------------------------------
def throughput_split():
    t = model.throughput_gap(I, B)
    rows = [("Users per\nstore", t["i_users"] / 1e3, t["b_users"] / 1e3, "{:.1f}k"),
            ("Orders per user\nper month", I.freq_per_month, B.freq_per_month, "{:.2f}"),
            ("Orders per\nstore per day", t["i_orders"], t["b_orders"], "{:,.0f}")]
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.6))
    for ax, (lab, iv, bv, fmt) in zip(axes, rows):
        ax.bar([0, 1], [iv, bv], color=[INSTAMART, BLINKIT], width=0.62)
        for x, v in [(0, iv), (1, bv)]:
            ax.text(x, v * 1.02, fmt.format(v), ha="center", va="bottom", fontweight="bold", color=INK)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Instamart", "Blinkit"])
        ax.set_yticks([])
        ax.grid(False)
        ax.set_ylim(0, max(iv, bv) * 1.22)
        ax.set_title(lab, fontsize=12.5)
        gap = bv / iv - 1
        ax.text(0.5, max(iv, bv) * 1.13, f"+{gap:.0%}", ha="center", color=INK2, fontsize=11)
    fig.suptitle(f"Frequency explains {t['freq_share']:.0%} of the throughput gap, users per store {t['users_share']:.0%}",
                 x=0.01, ha="left", fontsize=13.5, fontweight="bold", color=INK)
    save(fig, "03_throughput_split")


# 4. Three floors of break-even ---------------------------------------------------
def breakeven_floors():
    x = np.linspace(4.5, 12.5, 200) * 1e5
    vm, semi, fixed = S["var_margin"], S["semi_fixed"], S["fixed"]
    vm2 = model.with_levers(S, 24.5)
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ax.plot(x / 1e5, (x * vm - semi) / 1e3, color=INSTAMART, label="Contribution, today's margins")
    ax.plot(x / 1e5, (x * vm - semi - fixed) / 1e3, color=INSTAMART, ls=(0, (2, 2)), lw=1.8,
            label="Adj. EBITDA, today's margins")
    ax.plot(x / 1e5, (x * vm2 - semi - fixed) / 1e3, color=INK, lw=2.2,
            label="Adj. EBITDA with Swiggy's per-order levers (ads, mix, 1P: +₹24.5/order)")
    ax.axhline(0, color=INK2, lw=1)
    be1 = S["breakeven_nov_contribution"] / 1e5
    be3 = (semi + fixed) / vm2 / 1e5
    for xv, lab, dy in [(S["nov"] / 1e5, f"Today\n₹{S['nov']/1e5:.2f}L", -48), (P["new_nov"] / 1e5, f"After plan\n₹{P['new_nov']/1e5:.2f}L", -48)]:
        ax.axvline(xv, color=MUTED, lw=1, ls=(0, (3, 3)))
        ax.text(xv, -108, lab, ha="center", va="bottom", fontsize=10.5, color=INK2,
                bbox=dict(boxstyle="square,pad=0.2", fc=SURF, ec="none"))
    ax.plot([be1], [0], "o", ms=10, color=INSTAMART, mec=SURF, mew=2, zorder=5)
    ax.annotate(f"Floor 1: store contribution\nbreaks even at ₹{be1:.2f}L", (be1, 0), xytext=(be1 + 0.35, 22),
                fontsize=11, color=INK, fontweight="bold", arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.plot([be3], [0], "o", ms=10, color=INK, mec=SURF, mew=2, zorder=5)
    ax.annotate(f"Floor 3: company Adj. EBITDA\nbreaks even near ₹{be3:.1f}L", (be3, 0), xytext=(be3 + 0.45, -8), va="top",
                fontsize=11, color=INK, fontweight="bold", arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.set_xlim(4.5, 12.5)
    ax.set_ylim(-115, 75)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lakh))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: rs(v, unit="k")))
    ax.set_xlabel("NOV per store per day")
    ax.set_title("Profit per store per day (₹ '000) at each level of throughput")
    ax.legend(loc="upper left", fontsize=10.5)
    save(fig, "04_breakeven_floors")


# 5. Share of stores above their own break-even -----------------------------------
def store_distribution():
    sd = model.ASSUMPTIONS["store_nov_sd_lakh"]
    be = S["breakeven_nov_contribution"] / 1e5
    x = np.linspace(0, 13, 400)

    def pdf(mu):
        return np.array([exp(-((v - mu) ** 2) / (2 * sd ** 2)) / (sd * sqrt(2 * pi)) for v in x])

    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    for mu, col, lab, share, alpha, tx, ha in [
            (S["nov"] / 1e5, MUTED, "Today", P["share_cm_positive_before"], 0.25, 2.2, "center"),
            (P["new_nov"] / 1e5, INSTAMART, "After plan", P["share_cm_positive_after"], 0.30, 10.0, "center")]:
        y = pdf(mu)
        ax.plot(x, y, color=col, lw=2.2)
        ax.fill_between(x, y, where=x >= be, color=col, alpha=alpha, lw=0)
        ax.text(tx, y.max() * 0.93, f"{lab}\n{share:.0%} of stores\ncontribution-positive", ha=ha,
                fontsize=11.5, color=INK, fontweight="bold")
    ax.axvline(be, color=INK, lw=1.2)
    ax.text(be - 0.12, 0.012, f"store break-even\n₹{be:.2f}L", ha="right", fontsize=10.5, color=INK2)
    ax.set_yticks([])
    ax.grid(False)
    ax.set_ylim(0, 0.29)
    ax.set_xlim(0.5, 12.5)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lakh))
    ax.set_xlabel("NOV per store per day (illustrative spread across the 1,171 stores)")
    ax.set_title("Moving the whole network ₹1 lakh to the right")
    save(fig, "05_store_distribution")


# 6. Where the ₹1 lakh comes from -------------------------------------------------
def lever_stack():
    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    labels = ["Today"] + [n for n, _, _ in P["stack"]] + ["After plan"]
    run = S["nov"] / 1e3
    ax.bar(0, run, color=MUTED, width=0.62)
    ax.text(0, run + 6, f"₹{run/100:.2f}L", ha="center", fontweight="bold", color=INK)
    for k, (n, v, o) in enumerate(P["stack"], start=1):
        ax.bar(k, v / 1e3, bottom=run, color=INSTAMART, width=0.62)
        sub = f"+{o:.0f} orders" if o else "+₹15 basket"
        ax.text(k, run + v / 1e3 + 6, f"+₹{v/1e3:.0f}k\n{sub}", ha="center", fontsize=10.5, color=INK)
        ax.plot([k - 1 + 0.31, k - 0.31], [run, run], color=INK2, lw=0.8)
        run += v / 1e3
    k = len(labels) - 1
    ax.plot([k - 1 + 0.31, k - 0.31], [run, run], color=INK2, lw=0.8)
    ax.bar(k, run, color=INSTAMART, width=0.62)
    ax.text(k, run + 6, f"₹{run/100:.2f}L", ha="center", fontweight="bold", color=INK)
    ax.set_ylim(450, 720)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([l.replace(" + ", " +\n").replace("Swiggy-to-Mart ", "Swiggy-to-Mart\n").replace("Win back ", "Win back\n")
                        for l in labels], fontsize=10.5)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"₹{v/100:.1f}L"))
    ax.set_title("NOV per store per day, average Instamart store (axis starts at ₹4.5L)")
    save(fig, "06_lever_stack")


# 7. Which plays, and which not ---------------------------------------------------
def prioritisation():
    plays = [  # name, ease 1-5, impact ₹k NOV/store/day, chosen, label offset (dx, dy), ha
        ("Morning Ritual + fresh", 3.0, 48, True, (0.14, 0), "left"),
        ("Win back the lapsed", 4.2, 21, True, (0, 3.2), "center"),
        ("Bigger basket (No!ce, Switch)", 3.4, 19, True, (-0.14, 0), "right"),
        ("Swiggy-to-Mart bridge", 4.45, 15.5, True, (0, -3.4), "center"),
        ("Retune radius of\nunder-used stores", 2.0, 15, False, (0.14, 0), "left"),
        ("Afternoon fee holiday", 3.9, 7, False, (0.14, 0), "left"),
        ("Blanket free delivery\n(margin-negative: rents demand,\ndoesn't build habit)", 4.8, 31, False, (-0.14, 0), "right"),
        ("Sub-10-minute promise\n(regulatory headwind since Jan-26)", 1.0, 6, False, (0.14, 0), "left"),
        ("New stores in the\nsame micro-markets", 2.2, -10, False, (0.14, 0), "left"),
    ]
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ax.axvline(3, color=GRID, lw=1)
    ax.axhline(15, color=GRID, lw=1)
    for n, e, imp, chosen, (dx, dy), ha in plays:
        col = INSTAMART if chosen else MUTED
        ax.scatter(e, imp, s=360 if chosen else 220, color=col, edgecolor=SURF, linewidth=2, zorder=3)
        ax.text(e + dx, imp + dy, n, va="center", ha=ha, fontsize=10.5, color=INK if chosen else INK2,
                fontweight="bold" if chosen else "normal")
    ax.set_xlim(0.6, 5.2)
    ax.set_ylim(-16, 56)
    ax.set_xticks([1, 3, 5])
    ax.set_xticklabels(["Hard / slow", "", "Easy / fast"])
    ax.set_ylabel("NOV added per store per day (₹ '000)")
    ax.grid(False)
    ax.set_title("Candidate plays: orange = in the plan, grey = parked or rejected")
    save(fig, "07_prioritisation")


# 8. Build scale or earn it -------------------------------------------------------
def expand_vs_densify():
    rows = [("At today's ₹5.52L", P["stores_needed_today"], MUTED),
            (f"After this plan, ₹{P['new_nov']/1e5:.2f}L", P["stores_needed_after"], INSTAMART),
            ("At Blinkit's ₹11L target", 60_000 * 1e7 / (11e5 * 365), BLINKIT)]
    fig, ax = plt.subplots(figsize=(9.0, 3.8))
    for y, (lab, v, col) in enumerate(rows[::-1]):
        ax.barh(y, v, color=col, height=0.56)
        ax.text(v + 40, y, f"{v:,.0f} stores", va="center", fontweight="bold", color=INK)
    ax.axvline(P["stores"], color=INK, lw=1.2, ls=(0, (3, 3)))
    ax.text(P["stores"] + 30, 0.5, f"network today: {P['stores']:,}", fontsize=10.5, color=INK2, va="center")
    ax.set_yticks(range(3))
    ax.set_yticklabels([r[0] for r in rows[::-1]])
    ax.set_xlim(0, 3500)
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_title("Dark stores needed to reach ₹60,000 Cr annual NOV (Swiggy's break-even scale)")
    save(fig, "08_expand_vs_densify")


# 9. What Q2FY27 says -------------------------------------------------------------
def postscript():
    ps = pd.read_csv(Path(__file__).resolve().parent / "data" / "q2fy27_postscript.csv").set_index("metric")
    steps = [("Q1FY27", -20), ("Habit & reactivation\npricing", -100), ("New-user &\nfestive mix", -40),
             ("Fuller stores\n(orders/store +9.5%)", 60), ("Q2FY27", -100)]
    fig, ax = plt.subplots(figsize=(9.0, 4.3))
    run = 0
    for k, (lab, v) in enumerate(steps):
        if k in (0, len(steps) - 1):
            ax.bar(k, v, color=INSTAMART if k else MUTED, width=0.6)
            ax.text(k, v - 6, f"{v/100:+.1f}%".replace("-", "−"), ha="center", va="top", fontweight="bold", color=INK)
            run = v
        else:
            col = GAIN if v > 0 else LOSS
            ax.bar(k, v, bottom=run, color=col, width=0.6)
            ax.text(k, (run + v) - 6 if v < 0 else run + v + 6, f"{v:+.0f} bps".replace("-", "−"), ha="center",
                    va="top" if v < 0 else "bottom", fontweight="bold", color=INK)
            ax.plot([k - 1 + 0.3, k - 0.3], [run, run], color=INK2, lw=0.8)
            run += v
    ax.plot([len(steps) - 2 + 0.3, len(steps) - 1 - 0.3], [run, run], color=INK2, lw=0.8)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_ylim(-200, 40)
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s[0] for s in steps], fontsize=10.5)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v/100:.1f}%".replace("-", "−")))
    ax.set_title("Instamart contribution margin, % of GOV: what moved it in Q2FY27")
    o1, o2 = ps.loc["orders_per_store_day", ["q1fy27", "q2fy27"]].astype(float)
    ax.text(4.35, 22, f"orders/store/day {o1:,.0f} → {o2:,.0f}", ha="right", fontsize=10.5, color=INK2)
    save(fig, "09_q2fy27_postscript")


if __name__ == "__main__":
    for f in [throughput, per_order_gap, throughput_split, breakeven_floors, store_distribution,
              lever_stack, prioritisation, expand_vs_densify, postscript]:
        f()
        print("drew", f.__name__)
