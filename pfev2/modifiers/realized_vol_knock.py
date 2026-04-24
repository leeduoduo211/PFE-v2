from __future__ import annotations

import numpy as np

from pfev2.core.exceptions import ModifierError
from pfev2.modifiers.base import BaseModifier
from pfev2.modifiers.knock_out import _get_monitored_prices, _validate_observation_params


def _realized_vol(path_history: np.ndarray, monitor_pos: int, annualization_factor: float) -> np.ndarray:
    """Compute per-path annualized realized vol from path_history.

    Parameters
    ----------
    path_history : (n_paths, n_steps, n_trade_assets)
    monitor_pos  : index into the last axis (trade-asset position)
    annualization_factor : steps per year (252 daily, 52 weekly, 12 monthly)

    Returns
    -------
    (n_paths,) array of annualized realized volatilities
    """
    prices = path_history[:, :, monitor_pos]  # (n_paths, n_steps)
    n_rets = prices.shape[1] - 1
    if n_rets < 1:
        return np.zeros(prices.shape[0])
    log_rets = np.log(prices[:, 1:] / prices[:, :-1])  # (n_paths, n_rets)
    ddof = 1 if n_rets > 1 else 0
    return np.std(log_rets, axis=1, ddof=ddof) * np.sqrt(annualization_factor)


class RealizedVolKnockOut(BaseModifier):
    """Knock-out modifier based on realized volatility of the path.

    The payoff is zeroed for any path whose realized vol exceeds (or falls
    below) ``vol_barrier``.

    Parameters
    ----------
    inner : BaseInstrument
        The wrapped instrument.
    vol_barrier : float
        Annualized volatility threshold (e.g. 0.30 for 30%).
    direction : "above" | "below"
        "above" → knocked out when realized_vol > vol_barrier (high-vol KO).
        "below" → knocked out when realized_vol < vol_barrier (low-vol KO).
    asset_idx : int or None
        Global asset index to monitor. Defaults to the trade's first asset.
    annualization_factor : float
        Steps per year used in the inner MC grid (252 daily, 52 weekly,
        12 monthly). Must match the grid frequency used at pricing time.
    observation_style : "continuous" | "discrete" | "window"
        Controls which portion of the path is used to compute realized vol.
    observation_dates : list or None
        Required when observation_style="discrete".
    window_start : float or None
        Required when observation_style="window".
    window_end : float or None
        Required when observation_style="window".
    """

    def __init__(
        self,
        inner,
        vol_barrier: float,
        direction: str,
        asset_idx=None,
        annualization_factor: float = 52.0,
        observation_style: str = "continuous",
        observation_dates=None,
        window_start=None,
        window_end=None,
    ):
        super().__init__(inner)
        if direction not in ("above", "below"):
            raise ModifierError(f"direction must be 'above' or 'below', got '{direction}'")
        if vol_barrier <= 0:
            raise ModifierError(f"vol_barrier must be positive, got {vol_barrier}")
        if annualization_factor <= 0:
            raise ModifierError(f"annualization_factor must be positive, got {annualization_factor}")
        _validate_observation_params(observation_style, observation_dates, window_start, window_end)
        self.vol_barrier = vol_barrier
        self.direction = direction
        self.annualization_factor = annualization_factor
        self.observation_style = observation_style
        self.observation_dates = observation_dates
        self.window_start = window_start
        self.window_end = window_end
        self._monitor_pos = 0 if asset_idx is None else list(inner.asset_indices).index(asset_idx)

    def _apply(self, raw_payoff, spots, path_history, t_grid=None) -> np.ndarray:
        prices = path_history[:, :, self._monitor_pos]
        monitored = _get_monitored_prices(
            prices, self.observation_style, t_grid,
            self.observation_dates, self.window_start, self.window_end
        )
        # Reconstruct a 3-D history with only the monitored steps so
        # _realized_vol can index into axis 2 at position 0.
        filtered_history = monitored[:, :, np.newaxis]
        rv = _realized_vol(filtered_history, 0, self.annualization_factor)
        if self.direction == "above":
            knocked_out = rv > self.vol_barrier
        else:
            knocked_out = rv < self.vol_barrier
        return np.where(knocked_out, 0.0, raw_payoff)


class RealizedVolKnockIn(BaseModifier):
    """Knock-in modifier based on realized volatility of the path.

    The payoff is paid only for paths whose realized vol exceeds (or falls
    below) ``vol_barrier``.

    Parameters
    ----------
    inner : BaseInstrument
        The wrapped instrument.
    vol_barrier : float
        Annualized volatility threshold (e.g. 0.30 for 30%).
    direction : "above" | "below"
        "above" → activated when realized_vol > vol_barrier (high-vol KI).
        "below" → activated when realized_vol < vol_barrier (low-vol KI).
    asset_idx : int or None
        Global asset index to monitor. Defaults to the trade's first asset.
    annualization_factor : float
        Steps per year used in the inner MC grid (252 daily, 52 weekly,
        12 monthly). Must match the grid frequency used at pricing time.
    observation_style : "continuous" | "discrete" | "window"
        Controls which portion of the path is used to compute realized vol.
    observation_dates : list or None
        Required when observation_style="discrete".
    window_start : float or None
        Required when observation_style="window".
    window_end : float or None
        Required when observation_style="window".
    """

    def __init__(
        self,
        inner,
        vol_barrier: float,
        direction: str,
        asset_idx=None,
        annualization_factor: float = 52.0,
        observation_style: str = "continuous",
        observation_dates=None,
        window_start=None,
        window_end=None,
    ):
        super().__init__(inner)
        if direction not in ("above", "below"):
            raise ModifierError(f"direction must be 'above' or 'below', got '{direction}'")
        if vol_barrier <= 0:
            raise ModifierError(f"vol_barrier must be positive, got {vol_barrier}")
        if annualization_factor <= 0:
            raise ModifierError(f"annualization_factor must be positive, got {annualization_factor}")
        _validate_observation_params(observation_style, observation_dates, window_start, window_end)
        self.vol_barrier = vol_barrier
        self.direction = direction
        self.annualization_factor = annualization_factor
        self.observation_style = observation_style
        self.observation_dates = observation_dates
        self.window_start = window_start
        self.window_end = window_end
        self._monitor_pos = 0 if asset_idx is None else list(inner.asset_indices).index(asset_idx)

    def _apply(self, raw_payoff, spots, path_history, t_grid=None) -> np.ndarray:
        prices = path_history[:, :, self._monitor_pos]
        monitored = _get_monitored_prices(
            prices, self.observation_style, t_grid,
            self.observation_dates, self.window_start, self.window_end
        )
        filtered_history = monitored[:, :, np.newaxis]
        rv = _realized_vol(filtered_history, 0, self.annualization_factor)
        if self.direction == "above":
            activated = rv > self.vol_barrier
        else:
            activated = rv < self.vol_barrier
        return np.where(activated, raw_payoff, 0.0)
