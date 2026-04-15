import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class WorstOfCall(BaseInstrument):
    """Worst-of call option on a basket of assets.

    Category: Multi-asset
    Path required: No

    Payoff: max(min_i(S_i(T) / K_i) - 1, 0)

    The payoff is driven by the asset with the worst relative performance.
    Strikes are expressed as initial levels (performance is normalised).

    Parameters
    ----------
    strikes : array-like of float
        Reference (initial) levels for each asset. Length must match
        ``asset_indices``.
    """

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
    """Worst-of put option on a basket of assets.

    Category: Multi-asset
    Path required: No

    Payoff: max(1 - min_i(S_i(T) / K_i), 0)

    The payoff is driven by the asset with the worst relative performance.
    Strikes are expressed as initial levels (performance is normalised).

    Parameters
    ----------
    strikes : array-like of float
        Reference (initial) levels for each asset. Length must match
        ``asset_indices``.
    """

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
    """Best-of call option on a basket of assets.

    Category: Multi-asset
    Path required: No

    Payoff: max(max_i(S_i(T) / K_i) - 1, 0)

    The payoff is driven by the asset with the best relative performance.
    Strikes are expressed as initial levels (performance is normalised).

    Parameters
    ----------
    strikes : array-like of float
        Reference (initial) levels for each asset. Length must match
        ``asset_indices``.
    """

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
    """Best-of put option on a basket of assets.

    Category: Multi-asset
    Path required: No

    Payoff: max_i(max(1 - S_i(T) / K_i, 0))

    Pays the highest individual put payoff across all assets — each asset's
    put is evaluated independently and the maximum is taken.

    Parameters
    ----------
    strikes : array-like of float
        Reference (initial) levels for each asset. Length must match
        ``asset_indices``.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != len(asset_indices):
            raise InstrumentError("strikes length must match asset_indices length")
        self.strikes = np.array(strikes, dtype=float)

    def payoff(self, spots, path_history=None, t_grid=None):
        individual_put_payoffs = np.maximum(1.0 - spots / self.strikes, 0.0)
        return np.max(individual_put_payoffs, axis=1)
