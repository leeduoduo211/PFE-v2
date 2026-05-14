import numpy as np

from pfev2.core.types import PFEConfig
from pfev2.risk.result import PFEResult


def test_peak_pfe():
    result = PFEResult(
        time_points=np.array([0.0, 0.25, 0.5, 0.75, 1.0]),
        pfe_curve=np.array([0.0, 10.0, 20.0, 15.0, 5.0]),
        epe_curve=np.array([0.0, 5.0, 10.0, 8.0, 3.0]),
        peak_pfe=20.0,
        eepe=0.0,
        mtm_matrix=np.zeros((10, 5)),
        config=PFEConfig(),
        computation_time=1.0,
    )
    assert result.peak_pfe == 20.0


def test_summary_string():
    result = PFEResult(
        time_points=np.array([0.0, 1.0]),
        pfe_curve=np.array([0.0, 100.0]),
        epe_curve=np.array([0.0, 50.0]),
        peak_pfe=100.0,
        eepe=50.0,
        mtm_matrix=np.zeros((10, 2)),
        config=PFEConfig(),
        computation_time=5.0,
    )
    s = result.summary()
    assert "100" in s
    assert "50" in s


def _result_at(freq: str) -> PFEResult:
    return PFEResult(
        time_points=np.array([0.0, 0.5, 1.0]),
        pfe_curve=np.zeros(3),
        epe_curve=np.zeros(3),
        peak_pfe=0.0,
        eepe=0.0,
        mtm_matrix=np.zeros((1, 3)),
        config=PFEConfig(grid_frequency=freq),
        computation_time=0.0,
    )


def test_time_points_in_periods_matches_frequency():
    np.testing.assert_allclose(_result_at("weekly").time_points_in_periods(),
                               [0.0, 26.0, 52.0])
    np.testing.assert_allclose(_result_at("daily").time_points_in_periods(),
                               [0.0, 126.0, 252.0])
    np.testing.assert_allclose(_result_at("monthly").time_points_in_periods(),
                               [0.0, 6.0, 12.0])


def test_period_label_matches_frequency():
    assert _result_at("weekly").period_label() == "weeks"
    assert _result_at("daily").period_label() == "days"
    assert _result_at("monthly").period_label() == "months"


def test_time_points_in_weeks_is_alias():
    r = _result_at("monthly")
    np.testing.assert_array_equal(r.time_points_in_weeks(),
                                  r.time_points_in_periods())
