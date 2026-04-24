import numpy as np

from pfev2.modifiers.base import BaseModifier


class ObservationSchedule(BaseModifier):
    """Restricts path observation to a fixed discrete set of dates.

    Group: Structural

    Overrides ``observation_dates()`` so the simulation engine only evaluates
    the inner instrument at the specified dates. The payoff itself is passed
    through unchanged — this modifier purely controls *when* the path is
    sampled, not *what* is paid.

    Useful for wrapping path-dependent instruments (e.g., barriers, Asian
    options) that should be monitored on a pre-defined schedule rather than
    at every simulation step.

    Parameters
    ----------
    inner : BaseInstrument or BaseModifier
        The instrument to observe on the restricted schedule.
    dates : array-like of float
        Observation dates in years from trade inception. Will be converted
        to a numpy array.
    """

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
