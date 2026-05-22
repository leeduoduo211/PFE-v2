from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[2] / "ui" / "app.py"


def _trade_id_values(app):
    return [field.value for field in app.text_input if field.label == "Trade ID"]


def _click_button(app, label):
    for button in app.button:
        if button.label == label:
            button.click()
            return
    raise AssertionError(f"Button not found: {label}")


def test_add_trade_closes_builder_without_rendering_stale_fields():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()

    assert _trade_id_values(app) == ["TRD_001"]

    _click_button(app, "Add to Portfolio")
    app = app.run()

    assert _trade_id_values(app) == []
    assert app.session_state.filtered_state["_pending_next_trade_id"] == "TRD_002"
