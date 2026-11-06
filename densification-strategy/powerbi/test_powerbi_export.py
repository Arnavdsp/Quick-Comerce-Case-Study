"""
Recomputes the dashboard's DAX measures in Python, using only the exported CSVs,
and checks they land on the same numbers as the deck (model.py).
If this passes, a correctly built dashboard shows the deck's numbers at default slider values.
"""
from math import erf, sqrt
from pathlib import Path

import pandas as pd
import pytest

import export_powerbi
import model

DATA = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="module")
def t():
    export_powerbi.main()
    return {p.stem: pd.read_csv(p) for p in DATA.glob("*.csv")}


@pytest.fixture(scope="module")
def deck():
    _, i, b, _ = model.baseline()
    return model.plan(i), i, b


def ncdf(x, mu, sd):
    return 0.5 * (1 + erf((x - mu) / (sd * sqrt(2))))


def simulate(t, delivery=100, store_cost=38_000, levers=24.5, spend=10):
    """Same arithmetic as section 3 of measures.dax."""
    base = t["baseline"].iloc[0]
    plays = t["plays"][t["plays"].InPlan]
    var_margin = (base.StoreNOV_Day * base.CM_Pct + store_cost) / base.StoreNOV_Day
    uplift = plays.NOV_Day.sum() * delivery / 100
    added = plays.OrdersAdded_Day.sum() * delivery / 100
    new = base.StoreNOV_Day + uplift
    be = store_cost / var_margin
    annual_nov = uplift * base.Stores * 365 / 1e7
    net = annual_nov * var_margin - added * base.Stores * 365 * spend / 1e7
    needed = lambda nov: base.BreakevenNOV_Cr * 1e7 / (nov * 365)  # noqa: E731
    return dict(
        var_margin=var_margin, new=new,
        cm_after=(new * var_margin - store_cost) / new,
        pos_before=1 - ncdf(be, base.StoreNOV_Day, base.StoreSD),
        pos_after=1 - ncdf(be, new, base.StoreSD),
        annual_nov=annual_nov, net=net,
        avoided=needed(base.StoreNOV_Day) - needed(new),
        ebitda_be=(store_cost + base.HQFixed_Day) / (var_margin + levers / base.NetAOV) / 1e5,
        utilisation=base.Utilisation_Pct / 100 * (base.StoreOrders_Day + added) / base.StoreOrders_Day,
    )


def test_simulator_defaults_match_the_deck(t, deck):
    p, _, _ = deck
    s = simulate(t)
    assert s["new"] == pytest.approx(p["new_nov"], rel=1e-4)
    assert s["cm_after"] * 100 == pytest.approx(p["cm_pct_after"], abs=0.01)
    assert s["pos_before"] == pytest.approx(p["share_cm_positive_before"], abs=0.005)
    assert s["pos_after"] == pytest.approx(p["share_cm_positive_after"], abs=0.005)
    assert s["annual_nov"] == pytest.approx(p["annual_nov_cr"], rel=1e-4)
    assert s["net"] == pytest.approx(p["annual_net_cr"], rel=1e-3)
    assert s["avoided"] == pytest.approx(p["stores_avoided"], rel=1e-3)
    assert s["utilisation"] == pytest.approx(p["utilisation_after"] / 100, abs=0.005)
    assert round(s["ebitda_be"], 1) == 9.7


def test_half_delivery_matches_the_deck(t, deck):
    _, i, _ = deck
    half = model.plan(i, plays=model.scaled_plays(0.5))
    s = simulate(t, delivery=50)
    assert s["cm_after"] > 0
    # the basket play scales with orders in model.py but is a fixed ₹ value in the dashboard,
    # so allow a small difference at 50%
    assert s["net"] == pytest.approx(half["annual_net_cr"], rel=0.03)


def test_market_measures(t, deck):
    _, i, b = deck
    f = t["fact_quarterly"]
    q = f[f.Quarter == "Q1FY27"].set_index("Platform")
    nov_store_day = q.NOV_Cr * 100 / q.StoreDays
    assert nov_store_day["Instamart"] == pytest.approx(i.value_per_store_day_lakh, rel=1e-6)
    assert nov_store_day["Blinkit"] == pytest.approx(b.value_per_store_day_lakh, rel=1e-6)
    assert round(1 - nov_store_day["Instamart"] / nov_store_day["Blinkit"], 2) == 0.31
    freq = q.Orders_Mn / q.UserMonths_Mn
    assert round(freq["Instamart"], 2) == 2.83 and round(freq["Blinkit"], 2) == 3.47
    hq = q.HQFixed_Cr * 1e7 / q.StoreDays / 1000
    assert round(hq["Instamart"]) == 72 and round(hq["Blinkit"]) == 38
    share = q.NOV_Cr["Blinkit"] / q.NOV_Cr.sum()
    assert round(share, 2) == 0.75


def test_waterfalls_add_up(t, deck):
    gap = t["per_order_gap"]
    assert gap.Rs_per_Order.sum() == pytest.approx(deck[1].ebitda_per_order, abs=0.05)
    stack = t["lever_stack"]
    assert stack.NOV_k.sum() * 1e3 == pytest.approx(deck[0]["new_nov"], abs=10)


def test_tables_have_the_columns_the_guide_uses(t):
    need = {
        "fact_quarterly": {"Platform", "Quarter", "NOV_Cr", "Orders_Mn", "UserMonths_Mn", "StoreDays",
                           "Contribution_Cr", "AdjEBITDA_Cr", "HQFixed_Cr"},
        "plays": {"Play", "InPlan", "Status", "Ease", "NOV_Day", "Impact_k", "OrdersAdded_Day"},
        "baseline": {"Stores", "StoreNOV_Day", "StoreOrders_Day", "NetAOV", "CM_Pct", "HQFixed_Day", "StoreSD",
                     "CapexPerStore_Cr", "Utilisation_Pct", "BreakevenNOV_Cr", "AnnualEBITDALoss_Cr",
                     "BlinkitTargetNOV_Day"},
    }
    for name, cols in need.items():
        assert cols <= set(t[name].columns), name
