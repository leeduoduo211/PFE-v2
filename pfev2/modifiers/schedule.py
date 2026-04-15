import numpy as np
from pfev2.modifiers.base import BaseModifier


class ObservationSchedule(BaseModifier):
    """Restricts path observation to specific dates and overrides observation_dates()."""

    def __init__(self, inner, dates):
        super().__init__(inner)
        self._dates = np.asarray(dates)

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self._dates

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        return raw_payoff
