import numpy as np

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.base import BaseInstrument


class Dispersion(BaseInstrument):
    """Dispersion option: weighted component legs minus a basket leg.

    Category: Multi-asset
    Path required: No

    Payoff: sum(w_i * component_payoff_i) - basket_payoff

    where:
        component_payoff_i = max(S_i - K_i, 0) [call] or max(K_i - S_i, 0) [put]
        basket_spot = sum(w_i * S_i)
        basket_payoff = max(basket_spot - K_basket, 0) [call] or max(K_basket - basket_spot, 0) [put]

    Parameters
    ----------
    strikes : array-like of float
        Per-component strike levels. Length must match ``asset_indices``.
    weights : array-like of float
        Per-component weights. Must sum to 1.0.
    basket_strike : float
        Strike level for the basket leg.
    component_types : list of str
        ``"call"`` or ``"put"`` for each component leg.
    basket_type : str
        ``"call"`` or ``"put"`` for the basket leg.
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices,
                 strikes, weights, basket_strike, component_types, basket_type):
        super().__init__(trade_id, maturity, notional, asset_indices)
        n = len(asset_indices)
        strikes = np.array(strikes, dtype=float)
        weights = np.array(weights, dtype=float)

        # Validate lengths
        if len(strikes) != n:
            raise InstrumentError(
                f"strikes length ({len(strikes)}) must match asset_indices length ({n})"
            )
        if len(weights) != n:
            raise InstrumentError(
                f"weights length ({len(weights)}) must match asset_indices length ({n})"
            )
        if len(component_types) != n:
            raise InstrumentError(
                f"component_types length ({len(component_types)}) must match "
                f"asset_indices length ({n})"
            )

        # Validate values
        if abs(weights.sum() - 1.0) > 1e-8:
            raise InstrumentError(
                f"weights must sum to 1.0, got {weights.sum():.10f}"
            )
        if np.any(strikes <= 0):
            raise InstrumentError("all strikes must be positive")
        if basket_strike <= 0:
            raise InstrumentError(
                f"basket_strike must be positive, got {basket_strike}"
            )
        for ct in component_types:
            if ct not in ("call", "put"):
                raise InstrumentError(
                    f"component_types entries must be 'call' or 'put', got '{ct}'"
                )
        if basket_type not in ("call", "put"):
            raise InstrumentError(
                f"basket_type must be 'call' or 'put', got '{basket_type}'"
            )

        self.strikes = strikes
        self.weights = weights
        self.basket_strike = float(basket_strike)
        self.component_types = list(component_types)
        self.basket_type = basket_type

    def payoff(self, spots, path_history=None, t_grid=None):
        # Component payoffs (vectorized across paths)
        weighted_sum = np.zeros(spots.shape[0])
        for i, ct in enumerate(self.component_types):
            s_i = spots[:, i]
            if ct == "call":
                p_i = np.maximum(s_i - self.strikes[i], 0.0)
            else:
                p_i = np.maximum(self.strikes[i] - s_i, 0.0)
            weighted_sum += self.weights[i] * p_i

        # Basket leg
        basket_spot = spots @ self.weights
        if self.basket_type == "call":
            basket_payoff = np.maximum(basket_spot - self.basket_strike, 0.0)
        else:
            basket_payoff = np.maximum(self.basket_strike - basket_spot, 0.0)

        return weighted_sum - basket_payoff
