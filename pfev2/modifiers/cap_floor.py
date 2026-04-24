import numpy as np

from pfev2.modifiers.base import BaseModifier


class PayoffCap(BaseModifier):
    """Caps the inner instrument's payoff at a fixed maximum.

    Group: Payoff shaper

    Applies element-wise: payoff_out = min(payoff_in, cap)

    Commonly used to limit upside on structured products (e.g., capped calls,
    range notes).

    Parameters
    ----------
    inner : BaseInstrument or BaseModifier
        The instrument whose payoff will be capped.
    cap : float
        Maximum payoff value (inclusive).
    """

    def __init__(self, inner, cap):
        super().__init__(inner)
        self.cap = cap

    @property
    def requires_full_path(self):
        return self._inner.requires_full_path

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        return np.minimum(raw_payoff, self.cap)


class PayoffFloor(BaseModifier):
    """Floors the inner instrument's payoff at a fixed minimum.

    Group: Payoff shaper

    Applies element-wise: payoff_out = max(payoff_in, floor)

    Commonly used to guarantee a minimum return (e.g., principal protection,
    floored notes).

    Parameters
    ----------
    inner : BaseInstrument or BaseModifier
        The instrument whose payoff will be floored.
    floor : float
        Minimum payoff value (inclusive). Often 0 for capital protection.
    """

    def __init__(self, inner, floor):
        super().__init__(inner)
        self.floor = floor

    @property
    def requires_full_path(self):
        return self._inner.requires_full_path

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        return np.maximum(raw_payoff, self.floor)
