import numpy as np
from pfev2.modifiers.base import BaseModifier
from pfev2.core.exceptions import ModifierError

_VALID_OBSERVATION_STYLES = ("continuous", "discrete", "window")


def _validate_observation_params(observation_style, observation_dates, window_start, window_end):
    if observation_style not in _VALID_OBSERVATION_STYLES:
        raise ModifierError(
            f"observation_style must be one of {_VALID_OBSERVATION_STYLES}, "
            f"got '{observation_style}'"
        )
    if observation_style == "discrete" and observation_dates is None:
        raise ModifierError(
            "observation_style='discrete' requires observation_dates to be provided"
        )
    if observation_style == "window" and (window_start is None or window_end is None):
        raise ModifierError(
            "observation_style='window' requires both window_start and window_end"
        )


def _get_monitored_prices(prices, observation_style, t_grid, observation_dates, window_start, window_end):
    """Filter path prices to the monitored subset based on observation_style.

    Parameters
    ----------
    prices : (n_paths, n_steps) array — already sliced to the monitored asset.
    observation_style : "continuous" | "discrete" | "window"
    t_grid : 1-D array of time points corresponding to path steps, or None.
    observation_dates : list/array of times for discrete monitoring, or None.
    window_start, window_end : float bounds for window monitoring, or None.

    Returns
    -------
    (n_paths, k) array where k <= n_steps.
    """
    if observation_style == "continuous":
        return prices
    if observation_style == "discrete":
        if t_grid is None:
            return prices
        obs = np.asarray(observation_dates)
        indices = np.searchsorted(t_grid, obs, side="right") - 1
        indices = np.clip(indices, 0, prices.shape[1] - 1)
        return prices[:, indices]
    if observation_style == "window":
        if t_grid is None:
            return prices
        mask = (t_grid >= window_start) & (t_grid <= window_end)
        return prices[:, mask]
    return prices


class KnockOut(BaseModifier):
    """Knock-out barrier modifier.

    Group: Barrier
    Observation styles: continuous, discrete, window

    Zeroes the inner payoff if the monitored asset price breaches the barrier
    at any point during the observation window. Optionally pays a fixed rebate
    when the knock-out event occurs.

    Parameters
    ----------
    inner : BaseInstrument or BaseModifier
        The wrapped instrument whose payoff is extinguished on knock-out.
    barrier : float
        Barrier level.
    direction : str
        "up" — knocks out if price rises above barrier.
        "down" — knocks out if price falls below barrier.
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
    rebate : float
        Fixed amount paid to the holder on knock-out. Defaults to 0.
    """

    def __init__(self, inner, barrier, direction, asset_idx=None,
                 observation_style="continuous", observation_dates=None,
                 window_start=None, window_end=None, rebate=0.0):
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
        self.rebate = rebate
        self._monitor_pos = 0 if asset_idx is None else list(inner.asset_indices).index(asset_idx)

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        prices = path_history[:, :, self._monitor_pos]
        monitored = _get_monitored_prices(
            prices, self.observation_style, t_grid,
            self.observation_dates, self.window_start, self.window_end
        )
        if self.direction == "up":
            breached = np.any(monitored > self.barrier, axis=1)
        else:
            breached = np.any(monitored < self.barrier, axis=1)
        return np.where(breached, self.rebate, raw_payoff)
