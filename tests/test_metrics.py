"""The README's headline numbers, recomputed from the same code the dashboard uses."""
import math

import pytest

import metrics as m


@pytest.fixture(scope="module")
def df():
    panel, zepto_q, *_ = m.load_raw()
    return m.build_long(panel, zepto_q)


def platform(df, name):
    return df[df.platform == name].set_index("quarter")


def test_blinkit_share_of_combined_nov(df):
    b, i = platform(df, "Blinkit"), platform(df, "Instamart")
    share = b.nov_cr / (b.nov_cr + i.nov_cr) * 100
    assert round(share["Q1FY25"]) == 63
    assert round(share["Q1FY27"]) == 75
    assert round(b.nov_cr["Q1FY27"] / b.nov_cr["Q1FY25"], 1) == 4.2
    assert round(i.nov_cr["Q1FY27"] / i.nov_cr["Q1FY25"], 1) == 2.4


def test_store_throughput_and_fixed_cost(df):
    b, i = platform(df, "Blinkit"), platform(df, "Instamart")
    assert round(b.value_per_store_day_lakh["Q1FY27"], 1) == 8.0
    assert round(i.value_per_store_day_lakh["Q1FY27"], 1) == 5.5
    assert round(b.fixed_per_store_day_k["Q1FY27"]) == 38
    assert round(i.fixed_per_store_day_k["Q1FY27"]) == 72


def test_order_frequency(df):
    assert round(platform(df, "Blinkit").freq_per_month["Q1FY27"], 2) == 3.47
    assert round(platform(df, "Instamart").freq_per_month["Q1FY27"], 2) == 2.83


def test_zepto_busy_stores_but_negative_per_order(df):
    z = platform(df, "Zepto")
    assert round(z.orders_per_store_day["Q4FY26"], -1) == 2140
    assert round(z.value_per_order["Q4FY26"]) == 387
    assert round(z.ebitda_per_order["Q4FY26"]) == -59


def test_growth_decomposition_adds_up(df):
    b = platform(df, "Blinkit")
    parts, total = m.growth_decomposition(b, "Q1FY26", "Q1FY27")
    assert sum(parts.values()) == pytest.approx(total)
    assert total == pytest.approx((b.nov_cr["Q1FY27"] / b.nov_cr["Q1FY26"] - 1) * 100)


def test_simulator_arithmetic():
    # 10M users x 3 orders/month x 3 months = 90M orders; x ₹500 = ₹4,500 Cr NOV
    r = m.instamart_ebitda(mtu_mn=10, freq=3, basket=500, cm_pct=5, fixed_cr=200, extra_cost_per_order=2)
    assert r["orders_mn"] == pytest.approx(90)
    assert r["nov_cr"] == pytest.approx(4500)
    assert r["contribution_cr"] == pytest.approx(4500 * 0.05 - 90e6 * 2 / 1e7)
    assert r["ebitda_cr"] == pytest.approx(r["contribution_cr"] - 200)
    assert r["annual_nov_cr"] == pytest.approx(18000)


def test_fmt_inr():
    assert m.fmt_inr(1234.5, 1, " Cr") == "₹1,234.5 Cr"
    assert m.fmt_inr(-59) == "−₹59"
    assert m.fmt_inr(math.nan) == "–"
    assert m.fmt_inr(None) == "–"
