"""
The numbers behind the densification plan.

Baseline is Q1FY27 (Apr-Jun 2026), same as the rest of the repo. Everything is
read from ../data through ../metrics.py so the two analyses can't drift apart.
The few things filings don't tell us (store-level cost split, the spread of
store throughput, how each play performs) are in ASSUMPTIONS, with a note on
where each one comes from. Change them there and every chart and slide moves.
"""
import sys
from math import erf, sqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import metrics as m  # noqa: E402

BASE_Q = "Q1FY27"
DAYS = 365

ASSUMPTIONS = {
    # Store rent + base staff + power + security, per store per day, ₹.
    # Swiggy books these inside contribution ("under-utilisation costs [of new
    # stores] are expensed in contribution margin", Q2FY27 letter).
    # Two ways to the same number:
    #   bottom-up: ~4,200 sq ft x ~₹100/sq ft/month rent (₹14k/day) + ~30 pickers,
    #   packers and shift leads (₹20k/day) + power/security/misc (₹4k/day) = ₹38k
    #   top-down: Q2FY27 orders/store/day +9.5% bought +60 bps of CM. If that's
    #   all fixed-cost absorption, S/NOV = 60bps / (1 - 1/1.095) = 6.9% of
    #   ₹5.52L = ₹38k.
    "store_semi_fixed_per_day": 38_000,
    # Spread of NOV/store/day across the network (₹ lakh, normal). Only used to
    # say what share of stores clear their own break-even. Chosen so that the
    # break-even line implied by the cost split leaves 45% of stores above it,
    # which is what Swiggy reported for Q1FY27.
    "store_nov_sd_lakh": 1.8,
    # Capex per new dark store, ₹ Cr. Blinkit's steady-state guidance incl.
    # warehousing. Instamart doesn't disclose its own.
    "capex_per_store_cr": 2.5,
    # Programme spend on the four plays, ₹ per incremental order, year one.
    # Roughly a third of the marginal contribution each extra order earns.
    "play_cost_per_incr_order": 10.0,
}

# The four plays, sized for an average store. Each line is (what changes, how big).
# Catchment numbers are per store: Q1FY27 MTU / stores.
PLAYS = {
    "Morning Ritual + fresh": dict(
        kind="frequency", uplift=0.25,
        why="Daily milk, bread, eggs, fruit and veg on a 6-9 am batched slot. "
            "+0.25 orders/user/month takes Instamart from 2.83 to 3.08, still below Blinkit's 3.47."),
    "Swiggy-to-Mart bridge": dict(
        kind="new_users", users=520, freq=2.0,
        why="Swiggy food users in the catchment who don't use Instamart. ~6.5k per store; "
            "convert 8% at a lower 2.0 orders/month."),
    "Win back the lapsed": dict(
        kind="new_users", users=580, freq=2.0,
        why="With ~61% month-1 retention, every store has a large pool of one-time users. "
            "Bring back ~580 per store at 2.0 orders/month."),
    "Bigger basket": dict(
        kind="basket", uplift_inr=15,
        why="+₹15 net AOV from No!ce/Switch private label and non-grocery adds. "
            "Measured on all orders after the other three plays."),
}


def norm_cdf(z):
    return 0.5 * (1 + erf(z / sqrt(2)))


def baseline():
    panel, zepto_q, *_ = m.load_raw()
    df = m.build_long(panel, zepto_q)
    guide = m.load_raw()[3].set_index(["platform", "metric"]).value
    i = df[df.platform == "Instamart"].set_index("quarter").loc[BASE_Q]
    b = df[df.platform == "Blinkit"].set_index("quarter").loc[BASE_Q]
    return df, i, b, guide


def store_pnl(i, a=ASSUMPTIONS):
    """Average Instamart store per day, split into variable and semi-fixed parts."""
    nov = i.value_per_store_day_lakh * 1e5
    aov = i.value_per_order
    orders = nov / aov
    contribution = i.cm_pct / 100 * nov
    semi = a["store_semi_fixed_per_day"]
    var_margin = (contribution + semi) / nov            # what each extra rupee of NOV keeps
    fixed = i.fixed_per_store_day_k * 1e3                # HQ, tech, brand: below contribution
    return dict(
        nov=nov, aov=aov, orders=orders, contribution=contribution, semi_fixed=semi,
        var_margin=var_margin, fixed=fixed, ebitda=contribution - fixed,
        breakeven_nov_contribution=semi / var_margin,
        breakeven_nov_ebitda=(semi + fixed) / var_margin,
        marginal_cm_per_order=var_margin * aov,
    )


def ebitda_per_store_day(nov, var_margin, semi, fixed):
    return nov * var_margin - semi - fixed


def per_order_gap(i, b, a=ASSUMPTIONS):
    """
    Blinkit vs Instamart Adj. EBITDA per order, split into:
      - HQ / fixed costs spread over fewer orders
      - store semi-fixed costs spread over fewer orders (same ₹/store-day assumed for both)
      - everything else in contribution: ads, take rate, 1P margin, discounts
    """
    semi = a["store_semi_fixed_per_day"]
    i_orders = i.value_per_store_day_lakh * 1e5 / i.value_per_order
    b_orders = b.value_per_store_day_lakh * 1e5 / b.value_per_order
    fixed_gap = i.fixed_per_order - b.fixed_per_order
    semi_gap = semi / i_orders - semi / b_orders
    total = b.ebitda_per_order - i.ebitda_per_order
    return {
        "Blinkit": b.ebitda_per_order,
        "HQ costs over fewer orders": -fixed_gap,
        "Store costs over fewer orders": -semi_gap,
        "Variable margin (ads, 1P, pricing)": -(total - fixed_gap - semi_gap),
        "Instamart": i.ebitda_per_order,
        "_volume_share": (fixed_gap + semi_gap) / total,
    }


def throughput_gap(i, b):
    """Orders/store/day = users per store x orders per user per day. Log split of the gap."""
    from math import log
    i_users = i.mtu_mn * 1e6 / i.stores_end
    b_users = b.mtu_mn * 1e6 / b.stores_end
    i_o = i_users * i.freq_per_month * 12 / DAYS
    b_o = b_users * b.freq_per_month * 12 / DAYS
    tot = log(b_o / i_o)
    return dict(
        i_users=i_users, b_users=b_users, i_orders=i_o, b_orders=b_o,
        users_share=log(b_users / i_users) / tot,
        freq_share=log(b.freq_per_month / i.freq_per_month) / tot,
    )


def lever_stack(i, plays=PLAYS):
    """₹ of NOV per store per day added by each play, in order."""
    users = i.mtu_mn * 1e6 / i.stores_end
    aov = i.value_per_order
    orders = i.value_per_store_day_lakh * 1e5 / aov
    out, extra_orders = [], 0.0
    for name, p in plays.items():
        if p["kind"] == "frequency":
            o = users * p["uplift"] * 12 / DAYS
            extra_orders += o
            out.append((name, o * aov, o))
        elif p["kind"] == "new_users":
            o = p["users"] * p["freq"] * 12 / DAYS
            extra_orders += o
            out.append((name, o * aov, o))
        elif p["kind"] == "basket":
            out.append((name, (orders + extra_orders) * p["uplift_inr"], 0.0))
    return out


def plan(i, a=ASSUMPTIONS, plays=PLAYS):
    """The whole +₹1 lakh story for the network, in one dict."""
    s = store_pnl(i, a)
    stack = lever_stack(i, plays)
    add_nov = sum(v for _, v, _ in stack)
    add_orders = sum(o for _, _, o in stack)
    stores = int(i.stores_end)
    new_nov = s["nov"] + add_nov
    new_contribution = new_nov * s["var_margin"] - s["semi_fixed"]

    # share of stores above their own contribution break-even, before and after
    sd = a["store_nov_sd_lakh"] * 1e5
    be = s["breakeven_nov_contribution"]
    share_before = 1 - norm_cdf((be - s["nov"]) / sd)
    share_after = 1 - norm_cdf((be - new_nov) / sd)

    annual_nov_cr = add_nov * stores * DAYS / 1e7
    annual_contribution_cr = annual_nov_cr * s["var_margin"]
    annual_play_cost_cr = add_orders * stores * DAYS * a["play_cost_per_incr_order"] / 1e7

    # how many stores it takes to reach ₹60k Cr annual NOV at a given throughput
    target_cr = 60_000

    def stores_needed(nov_per_day):
        return target_cr * 1e7 / (nov_per_day * DAYS)

    avoided = stores_needed(s["nov"]) - stores_needed(new_nov)
    return dict(
        store=s, stack=stack, add_nov=add_nov, add_orders=add_orders, new_nov=new_nov,
        cm_pct_before=s["contribution"] / s["nov"] * 100,
        cm_pct_after=new_contribution / new_nov * 100,
        contribution_after=new_contribution,
        share_cm_positive_before=share_before, share_cm_positive_after=share_after,
        annual_nov_cr=annual_nov_cr, annual_contribution_cr=annual_contribution_cr,
        annual_play_cost_cr=annual_play_cost_cr,
        annual_net_cr=annual_contribution_cr - annual_play_cost_cr,
        annual_ebitda_loss_cr=-i.adj_ebitda_cr * 4,
        stores_needed_today=stores_needed(s["nov"]), stores_needed_after=stores_needed(new_nov),
        stores_avoided=avoided, capex_avoided_cr=avoided * a["capex_per_store_cr"],
        utilisation_after=float(m.load_raw()[3].set_index(["platform", "metric"]).value
                                ["Instamart", "store_utilisation_pct"]) * (s["orders"] + add_orders) / s["orders"],
        stores=stores,
    )


def scaled_plays(factor, plays=PLAYS):
    """Same plays, each delivering `factor` of its planned effect (0.5 = half)."""
    out = {}
    for k, p in plays.items():
        q = dict(p)
        for f in ("uplift", "users", "uplift_inr"):
            if f in q:
                q[f] = q[f] * factor
        out[k] = q
    return out


def sensitivity(i):
    """CM after the plan, and share of CM-positive stores, across the two softest assumptions."""
    rows = []
    for semi in (30_000, 38_000, 45_000):
        for factor in (0.5, 1.0):
            a = dict(ASSUMPTIONS, store_semi_fixed_per_day=semi)
            p = plan(i, a, scaled_plays(factor))
            rows.append(dict(semi_k=semi / 1e3, delivery=factor, add_nov_lakh=p["add_nov"] / 1e5,
                             cm_after=p["cm_pct_after"], breakeven_lakh=p["store"]["breakeven_nov_contribution"] / 1e5,
                             net_cr=p["annual_net_cr"]))
    return rows


def with_levers(s, inr_per_order):
    """Variable margin once management's per-order levers (ads, mix, 1P) land."""
    return s["var_margin"] + inr_per_order / s["aov"]


if __name__ == "__main__":
    df, i, b, guide = baseline()
    p = plan(i)
    s = p["store"]
    print(f"Average store, {BASE_Q}: NOV ₹{s['nov']/1e5:.2f}L/day, {s['orders']:,.0f} orders, AOV ₹{s['aov']:.0f}")
    print(f"  variable margin {s['var_margin']:.1%} | semi-fixed ₹{s['semi_fixed']/1e3:.0f}k | HQ fixed ₹{s['fixed']/1e3:.1f}k")
    print(f"  contribution break-even ₹{s['breakeven_nov_contribution']/1e5:.2f}L | "
          f"EBITDA break-even (today's margins) ₹{s['breakeven_nov_ebitda']/1e5:.1f}L")
    print(f"  marginal contribution per extra order ₹{s['marginal_cm_per_order']:.1f}")
    g = per_order_gap(i, b)
    print("\nPer-order EBITDA gap:", {k: round(v, 1) for k, v in g.items()})
    t = throughput_gap(i, b)
    print("Throughput gap:", {k: round(v, 2) for k, v in t.items()})
    print("\nLever stack:")
    for n, v, o in p["stack"]:
        print(f"  {n:28s} +₹{v/1e3:5.1f}k  (+{o:.0f} orders)")
    print(f"  total +₹{p['add_nov']/1e5:.2f}L -> ₹{p['new_nov']/1e5:.2f}L, +{p['add_orders']:.0f} orders/day")
    print(f"\nCM {p['cm_pct_before']:+.2f}% -> {p['cm_pct_after']:+.2f}% of NOV")
    print(f"Stores CM-positive {p['share_cm_positive_before']:.0%} -> {p['share_cm_positive_after']:.0%}")
    print(f"Utilisation ~{p['utilisation_after']:.0f}%")
    print(f"Annual: +₹{p['annual_nov_cr']:,.0f} Cr NOV, +₹{p['annual_contribution_cr']:,.0f} Cr contribution, "
          f"−₹{p['annual_play_cost_cr']:,.0f} Cr play cost = ₹{p['annual_net_cr']:,.0f} Cr net "
          f"(vs ₹{p['annual_ebitda_loss_cr']:,.0f} Cr annual EBITDA loss)")
    print(f"Stores for ₹60k Cr: {p['stores_needed_today']:,.0f} at today's throughput vs "
          f"{p['stores_needed_after']:,.0f} after -> {p['stores_avoided']:,.0f} fewer, ₹{p['capex_avoided_cr']:,.0f} Cr capex")
    print("\nSensitivity:")
    for r in sensitivity(i):
        print("  ", {k: round(v, 2) for k, v in r.items()})
    vm = with_levers(s, 24.5)
    print(f"\nWith ₹24.5/order of mgmt levers: var margin {vm:.1%}, "
          f"EBITDA break-even at ₹{(s['semi_fixed']+s['fixed'])/vm/1e5:.1f}L/store/day")
