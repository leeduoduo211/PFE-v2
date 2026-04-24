import numpy as np

from pfev2.core.exceptions import ModifierError
from pfev2.modifiers.base import BaseModifier
from pfev2.modifiers.knock_out import _get_monitored_prices, _validate_observation_params


class KnockIn(BaseModifier):
    """Knock-in barrier modifier.

    Group: Barrier
    Observation styles: continuous, discrete, window

    Activates the inner payoff only if the monitored asset price breaches the
    barrier at some point during the observation window. If the barrier is
    never touched, the payoff is zero.

    Parameters
    ----------
    inner : BaseInstrument or BaseModifier
        The wrapped instrument whose payoff is activated on knock-in.
    barrier : float
        Barrier level.
    direction : str
        "up" — knocks in if price rises above barrier.
        "down" — knocks in if price falls below barrier.
    asset_idx : int, optional
        Global asset index to monitor. Defaults to the first asset.
    observation_style : str
        "continuous" — full path monitored (default).
        "discrete" — monitored only on ``observation_dates``.
        "window" — monitored only between ``window_start`` and ``window_end``.
    observation_dates : array-like of float, optional
        Required when ``observation_style="discrete"``.
    window_start : float, optional
        Start of monitoring window (years). Required for ``style="window"``.
    window_end : float, optional
        End of monitoring window (years). Required for ``style="window"``.
    """

    def __init__(self, inner, barrier, direction, asset_idx=None,
                 observation_style="continuous", observation_dates=None,
                 window_start=None, window_end=None):
        super().__init__(inner)
        if direction not in ("up", "down"):
            raise ModifierError(f"direction must be 'up' or 'down', got '{direction}'")
        _validate_observation_params(observation_style, observation_dates, window_start, window_end)
        self.barrier = barrier
        self.direction = direction
        self.observation_style = observation_style
        self.observation_dates = observation_dates
        self.window_start = window_start
        self.window_end = window_end
        self._monitor_pos = 0 if asset_idx is None else list(inner.asset_indices).index(asset_idx)

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        prices = path_history[:, :, self._monitor_pos]
        monitored = _get_monitored_prices(
            prices, self.observation_style, t_grid,
            self.observation_dates, self.window_start, self.window_end
        )
        if self.direction == "up":
            activated = np.any(monitored > self.barrier, axis=1)
        else:
            activated = np.any(monitored < self.barrier, axis=1)
        return np.where(activated, raw_payoff, 0.0)
