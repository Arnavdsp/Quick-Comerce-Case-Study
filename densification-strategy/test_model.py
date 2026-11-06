"""Every number quoted in the deck and the write-up, recomputed."""
import pytest

import model


@pytest.fixture(scope="module")
def base():
    _, i, b, _ = model.baseline()
    return i, b


def test_average_store_today(base):
    i, _ = base
    s = model.store_pnl(i)
    assert round(s["nov"] / 1e5, 2) == 5.52
    assert round(s["orders"], -1) == 1090          # Swiggy reports 1,089
    assert round(s["var_margin"] * 100, 1) == 6.6
    assert round(s["breakeven_nov_contribution"] / 1e5, 2) == 5.76
    assert round(s["marginal_cm_per_order"], 1) == 33.5


def test_three_quarters_of_the_gap_is_volume(base):
    g = model.per_order_gap(*base)
    assert round(g["Blinkit"] - g["Instamart"]) == 71
    assert round(g["HQ costs over fewer orders"]) == -42
    assert round(g["Store costs over fewer orders"], 1) == -10.5
    assert 0.70 <= g["_volume_share"] <= 0.76
    parts = sum(v for k, v in g.items() if k not in ("Blinkit", "Instamart", "_volume_share"))
    assert g["Blinkit"] + parts == pytest.approx(g["Instamart"])


def test_throughput_gap_is_mostly_frequency(base):
    t = model.throughput_gap(*base)
    assert round(t["freq_share"], 2) == 0.63
    assert t["users_share"] + t["freq_share"] == pytest.approx(1)


def test_plan_adds_one_lakh_and_crosses_contribution_breakeven(base):
    i, _ = base
    p = model.plan(i)
    assert 1.0 <= p["add_nov"] / 1e5 <= 1.1
    assert p["cm_pct_before"] < 0 < p["cm_pct_after"]
    assert round(p["cm_pct_after"], 1) == 0.8
    assert round(p["share_cm_positive_before"], 2) == 0.45
    assert round(p["share_cm_positive_after"], 2) == 0.67
    assert p["utilisation_after"] < 50                 # still far from capacity


def test_annual_economics(base):
    i, _ = base
    p = model.plan(i)
    assert round(p["annual_nov_cr"], -2) == 4400
    assert round(p["annual_net_cr"], -1) == 220
    assert round(p["stores_avoided"], -1) == 470
    assert round(p["capex_avoided_cr"], -2) == 1200


def test_half_delivery_still_clears_breakeven(base):
    i, _ = base
    for row in model.sensitivity(i):
        assert row["cm_after"] > 0, row


def test_ebitda_breakeven_needs_more_than_densification(base):
    i, _ = base
    s = model.store_pnl(i)
    assert round(s["breakeven_nov_ebitda"] / 1e5) == 17
    vm = model.with_levers(s, 24.5)
    assert round((s["semi_fixed"] + s["fixed"]) / vm / 1e5, 1) == 9.7
