from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from pfev2.core.types import PFEConfig


@dataclass
class PFEResult:
    time_points: np.ndarray
    pfe_curve: np.ndarray
    epe_curve: np.ndarray
    peak_pfe: float
    eepe: float
    mtm_matrix: np.ndarray
    config: PFEConfig
    computation_time: float
    per_trade_mtm: Optional[np.ndarray] = None
    unmargined_pfe_curve: Optional[np.ndarray] = None
    unmargined_epe_curve: Optional[np.ndarray] = None

    def _periods_per_year(self) -> int:
        return {"daily": 252, "weekly": 52, "monthly": 12}.get(
            self.config.grid_frequency, 52
        )

    def _period_label(self) -> str:
        return {"daily": "days", "weekly": "weeks", "monthly": "months"}.get(
            self.config.grid_frequency, "weeks"
        )

    def time_points_in_weeks(self) -> np.ndarray:
        """Return time points converted from years to display periods.

        For weekly grids this is weeks (×52), daily grids days (×252),
        monthly grids months (×12).  The method name is kept for backwards
        compatibility; use ``_period_label()`` to get the correct unit string.
        """
        return self.time_points * self._periods_per_year()

    def summary(self) -> str:
        horizon = self.time_points[-1] * self._periods_per_year()
        label = self._period_label()
        lines = [
            f"Peak PFE:          {self.peak_pfe:,.2f}",
            f"EEPE:              {self.eepe:,.2f}",
            f"Confidence:        {self.config.confidence_level:.0%}",
            f"Outer paths:       {self.config.n_outer:,}",
            f"Inner paths:       {self.config.n_inner:,}",
            f"Margined:          {self.config.margined}",
            f"Horizon:           {horizon:.0f} {label}",
            f"Computation time:  {self.computation_time:.1f}s",
        ]
        return "\n".join(lines)
