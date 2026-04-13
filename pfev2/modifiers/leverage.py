import numpy as np
from pfev2.modifiers.base import BaseModifier


class LeverageModifier(BaseModifier):
    def __init__(self, inner, threshold, leverage):
        super().__init__(inner)
        self.threshold = threshold
        self.leverage = leverage

    @property
    def requires_full_path(self):
        return self._inner.requires_full_path

    def _apply(self, raw_payoff, spots, path_history):
        return np.where(raw_payoff > self.threshold, raw_payoff * self.leverage, raw_payoff)
