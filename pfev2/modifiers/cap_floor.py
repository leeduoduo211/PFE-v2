import numpy as np
from pfev2.modifiers.base import BaseModifier


class PayoffCap(BaseModifier):
    def __init__(self, inner, cap):
        super().__init__(inner)
        self.cap = cap

    @property
    def requires_full_path(self):
        return self._inner.requires_full_path

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        return np.minimum(raw_payoff, self.cap)


class PayoffFloor(BaseModifier):
    def __init__(self, inner, floor):
        super().__init__(inner)
        self.floor = floor

    @property
    def requires_full_path(self):
        return self._inner.requires_full_path

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        return np.maximum(raw_payoff, self.floor)
