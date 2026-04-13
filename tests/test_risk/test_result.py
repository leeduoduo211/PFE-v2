import numpy as np
from pfev2.risk.result import PFEResult
from pfev2.core.types import PFEConfig


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
