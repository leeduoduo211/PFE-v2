import numpy as np

from ui.components import dashboard_view, results_viewer


def _result(freq):
    return {
        "time_points": [0.0, 0.5, 1.0],
        "pfe_curve": [0.0, 1.0, 2.0],
        "epe_curve": [0.0, 0.5, 1.0],
        "config": {"grid_frequency": freq, "confidence_level": 0.95},
    }


def test_results_viewer_time_axis_respects_daily_grid():
    axis, label = results_viewer._time_axis(_result("daily"))
    assert label == "days"
    np.testing.assert_allclose(axis, [0.0, 126.0, 252.0])


def test_results_viewer_time_axis_respects_monthly_grid():
    axis, label = results_viewer._time_axis(_result("monthly"))
    assert label == "months"
    np.testing.assert_allclose(axis, [0.0, 6.0, 12.0])


def test_dashboard_time_axis_respects_monthly_grid():
    axis, label = dashboard_view._time_axis(_result("monthly"))
    assert label == "months"
    np.testing.assert_allclose(axis, [0.0, 6.0, 12.0])


def test_results_viewer_confidence_label_uses_configured_level():
    result = _result("daily")
    result["config"]["confidence_level"] = 0.99

    assert results_viewer._confidence_label(result) == "99th percentile"
