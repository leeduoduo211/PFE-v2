import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class WorstOfOption(BaseInstrument):
    """Worst-of option (call or put) on a basket of assets.

    Category: Multi-asset
    Path required: No

    Payoff:
        call: max(min_i(S_i(T) / K_i) - 1, 0)
        put:  max(1 - min_i(S_i(T) / K_i), 0)

    The payoff is driven by the asset with the worst relative performance.
    Both call and put use the same aggregation (min), just flipped.
    Strikes are expressed as initial levels (performance is normalised).

    Parameters
    ----------
    strikes : array-like of float
        Reference (initial) levels for each asset. Length must match
        ``asset_indices``.
    option_type : str
        ``"call"`` or ``"put"``.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes, option_type):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != len(asset_indices):
            raise InstrumentError("strikes length must match asset_indices length")
        if option_type not in ("call", "put"):
            raise InstrumentError(
                f"option_type must be 'call' or 'put', got '{option_type}'"
            )
        self.strikes = np.array(strikes, dtype=float)
        self.option_type = option_type

    def payoff(self, spots, path_history=None, t_grid=None):
        performances = spots / self.strikes
        worst = np.min(performances, axis=1)
        if self.option_type == "call":
            return np.maximum(worst - 1.0, 0.0)
        return np.maximum(1.0 - worst, 0.0)


class BestOfOption(BaseInstrument):
    """Best-of option (call or put) on a basket of assets.

    Category: Multi-asset
    Path required: No

    Payoff:
        call: max(max_i(S_i(T) / K_i) - 1, 0)
        put:  max_i(max(1 - S_i(T) / K_i, 0))

    **Important asymmetry**: The call aggregates performances then applies the
    option payoff, but the put evaluates each asset's put independently and
    takes the maximum payoff. The put is NOT ``max(1 - max_i(perf), 0)``.

    Parameters
    ----------
    strikes : array-like of float
        Reference (initial) levels for each asset. Length must match
        ``asset_indices``.
    option_type : str
        ``"call"`` or ``"put"``.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, strikes, option_type):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if len(strikes) != len(asset_indices):
            raise InstrumentError("strikes length must match asset_indices length")
        if option_type not in ("call", "put"):
            raise InstrumentError(
                f"option_type must be 'call' or 'put', got '{option_type}'"
            )
        self.strikes = np.array(strikes, dtype=float)
        self.option_type = option_type

    def payoff(self, spots, path_history=None, t_grid=None):
        performances = spots / self.strikes
        if self.option_type == "call":
            best = np.max(performances, axis=1)
            return np.maximum(best - 1.0, 0.0)
        # Put: evaluate individual puts FIRST, then take maximum
        individual_put_payoffs = np.maximum(1.0 - performances, 0.0)
        return np.max(individual_put_payoffs, axis=1)
