import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class WorstOfCall(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != len(asset_indices):
            raise InstrumentError("strikes length must match asset_indices length")
        self.strikes = np.array(strikes, dtype=float)

    def payoff(self, spots, path_history=None, t_grid=None):
        performances = spots / self.strikes
        worst = np.min(performances, axis=1)
        return np.maximum(worst - 1.0, 0.0)


class WorstOfPut(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != len(asset_indices):
            raise InstrumentError("strikes length must match asset_indices length")
        self.strikes = np.array(strikes, dtype=float)

    def payoff(self, spots, path_history=None, t_grid=None):
        performances = spots / self.strikes
        worst = np.min(performances, axis=1)
        return np.maximum(1.0 - worst, 0.0)


class BestOfCall(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != len(asset_indices):
            raise InstrumentError("strikes length must match asset_indices length")
        self.strikes = np.array(strikes, dtype=float)

    def payoff(self, spots, path_history=None, t_grid=None):
        performances = spots / self.strikes
        best = np.max(performances, axis=1)
        return np.maximum(best - 1.0, 0.0)


class BestOfPut(BaseInstrument):
    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != len(asset_indices):
            raise InstrumentError("strikes length must match asset_indices length")
        self.strikes = np.array(strikes, dtype=float)

    def payoff(self, spots, path_history=None, t_grid=None):
        individual_put_payoffs = np.maximum(1.0 - spots / self.strikes, 0.0)
        return np.max(individual_put_payoffs, axis=1)
