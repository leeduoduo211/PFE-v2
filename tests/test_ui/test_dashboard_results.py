from pathlib import Path

from ui.components import dashboard_view

ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_result_body_renderer_is_shared_entrypoint():
    assert hasattr(dashboard_view, "render_dashboard_result_body")


def test_wizard_results_tab_uses_original_results_summary():
    app_source = (ROOT / "ui" / "app.py").read_text(encoding="utf-8")

    assert "render_results_summary(latest)" in app_source
    assert "render_dashboard_result_body(latest" not in app_source


def test_view_mode_toggle_labels_dashboard_as_summary():
    app_source = (ROOT / "ui" / "app.py").read_text(encoding="utf-8")

    assert 'else "Summary"' in app_source
    assert 'else "Dashboard"' not in app_source
