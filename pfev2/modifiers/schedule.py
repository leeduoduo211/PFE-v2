import numpy as np

from pfev2.modifiers.base import BaseModifier


class ObservationSchedule(BaseModifier):
    """Restrict path observation to a fixed discrete set of dates.

    Group: Structural

    Filters the path passed to the wrapped instrument or modifier so it only
    contains the requested dates. Terminal spots are still passed separately to
    the wrapped payoff, but path monitoring is restricted to this schedule.

    Useful for wrapping path-dependent instruments (for example, barriers or
    double-no-touch trades) that should be monitored on a pre-defined schedule
    rather than at every simulation step.
    """

    def __init__(self, inner, dates):
        super().__init__(inner)
        self._dates = np.asarray(dates)

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self._dates

    def payoff(self, spots, path_history, t_grid=None):
        if path_history is None or t_grid is None:
            return self._inner.payoff(spots, path_history, t_grid)

        has_explicit_valuation = hasattr(t_grid, "valuation_time")
        grid = np.asarray(t_grid, dtype=float)
        if grid.size == 0 or self._dates.size == 0:
            return self._inner.payoff(spots, path_history, grid)

        dates = self._dates
        is_relative_remaining = (
            not has_explicit_valuation
            and abs(float(grid[0])) <= 1e-12
            and float(grid[-1]) < self.maturity - 1e-12
        )
        if is_relative_remaining:
            valuation_time = self.maturity - float(grid[-1])
            dates = dates - valuation_time
            dates = dates[dates > 1e-12]

        if dates.size == 0:
            return self._inner.payoff(spots, path_history[:, :0, :], grid[:0])

        obs_indices = np.searchsorted(grid, dates, side="right") - 1
        obs_indices = np.clip(obs_indices, 0, path_history.shape[1] - 1)

        indices = np.unique(obs_indices)
        filtered_history = path_history[:, indices, :]
        filtered_grid = grid[indices]
        return self._inner.payoff(spots, filtered_history, filtered_grid)

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        return raw_payoff
