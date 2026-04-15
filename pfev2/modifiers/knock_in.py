import numpy as np
from pfev2.modifiers.base import BaseModifier
from pfev2.core.exceptions import ModifierError
from pfev2.modifiers.knock_out import _validate_observation_params, _get_monitored_prices


class KnockIn(BaseModifier):
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
