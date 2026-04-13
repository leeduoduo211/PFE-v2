import numpy as np
from pfev2.modifiers.base import BaseModifier
from pfev2.core.exceptions import ModifierError


class KnockIn(BaseModifier):
    def __init__(self, inner, barrier, direction, asset_idx=None):
        super().__init__(inner)
        if direction not in ("up", "down"):
            raise ModifierError(f"direction must be 'up' or 'down', got '{direction}'")
        self.barrier = barrier
        self.direction = direction
        self._monitor_pos = 0 if asset_idx is None else list(inner.asset_indices).index(asset_idx)

    def _apply(self, raw_payoff, spots, path_history):
        prices = path_history[:, :, self._monitor_pos]
        if self.direction == "up":
            activated = np.any(prices > self.barrier, axis=1)
        else:
            activated = np.any(prices < self.barrier, axis=1)
        return np.where(activated, raw_payoff, 0.0)
