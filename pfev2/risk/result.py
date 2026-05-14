from __future__ import annotations

from dataclasses import dataclass

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
    per_trade_mtm: np.ndarray | None = None
    unmargined_pfe_curve: np.ndarray | None = None
    unmargined_epe_curve: np.ndarray | None = None

    def _periods_per_year(self) -> int:
        return {"daily": 252, "weekly": 52, "monthly": 12}.get(
            self.config.grid_frequency, 52
        )

    def _period_label(self) -> str:
        return {"daily": "days", "weekly": "weeks", "monthly": "months"}.get(
            self.config.grid_frequency, "weeks"
        )

    def time_points_in_periods(self) -> np.ndarray:
        """Return time points scaled to the display period of this grid.

        For weekly grids the result is in weeks (×52), daily in days
        (×252), monthly in months (×12). The unit is given by
        :meth:`period_label`.
        """
        return self.time_points * self._periods_per_year()

    def period_label(self) -> str:
        """Return the display unit string for ``time_points_in_periods``."""
        return self._period_label()

    def time_points_in_weeks(self) -> np.ndarray:
        """Deprecated alias of :meth:`time_points_in_periods`.

        Kept because UI code calls it by name; despite the name, it returns
        days for daily grids and months for monthly grids. New code should
        prefer :meth:`time_points_in_periods` plus :meth:`period_label`.
        """
        return self.time_points_in_periods()

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
