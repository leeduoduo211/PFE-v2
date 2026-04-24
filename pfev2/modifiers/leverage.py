import numpy as np

from pfev2.modifiers.base import BaseModifier


class LeverageModifier(BaseModifier):
    """Applies a leverage multiplier to payoffs that exceed a threshold.

    Group: Payoff shaper

    Applies element-wise:
        payoff_out = payoff_in * leverage  if payoff_in > threshold
        payoff_out = payoff_in             otherwise

    Useful for modelling participation rates or enhanced return structures
    above a given payoff level.

    Parameters
    ----------
    inner : BaseInstrument or BaseModifier
        The instrument whose payoff will be leveraged.
    threshold : float
        Payoff level above which the leverage multiplier is applied.
    leverage : float
        Multiplier applied to payoffs above the threshold.
    """

    def __init__(self, inner, threshold, leverage):
        super().__init__(inner)
        self.threshold = threshold
        self.leverage = leverage

    @property
    def requires_full_path(self):
        return self._inner.requires_full_path

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        return np.where(raw_payoff > self.threshold, raw_payoff * self.leverage, raw_payoff)
