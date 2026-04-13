import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class DoubleNoTouch(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, lower, upper):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if lower >= upper:
            raise InstrumentError(f"lower ({lower}) must be < upper ({upper})")
        self.lower = lower
        self.upper = upper

    @property
    def requires_full_path(self) -> bool:
        return True

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        path_min = np.min(prices, axis=1)
        path_max = np.max(prices, axis=1)
        no_touch = (path_min >= self.lower) & (path_max <= self.upper)
        return no_touch.astype(float)
