"""Runs the dashboard headlessly and checks no tab or widget raises."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(scope="module")
def app():
    return AppTest.from_file(APP, default_timeout=120).run()


def test_app_renders_every_tab(app):
    assert not app.exception
    assert [t.label for t in app.tabs] == [
        "Market", "Store economics", "Per-order P&L", "Customers",
        "Break-even simulator", "Industry & timeline", "Data & method",
    ]


def test_every_slider_can_move_to_its_extremes(app):
    for slider in app.slider:
        for value in (slider.min, slider.max):
            slider.set_value(value).run()
            assert not app.exception, f"{slider.label} = {value}"


def test_every_selectbox_option_renders(app):
    for box in app.selectbox:
        for option in box.options:
            box.set_value(option).run()
            assert not app.exception, f"{box.label} = {option}"
