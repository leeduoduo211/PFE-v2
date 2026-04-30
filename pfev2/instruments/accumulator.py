import numpy as np

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.base import BaseInstrument


class Accumulator(BaseInstrument):
    """Accumulator (buy) or decumulator (sell) — periodic forward obligation.

    Category: Periodic
    Path required: Yes

    At each scheduled observation date the holder accumulates (or decumulates)
    units of the underlying at the fixed strike:

        side="buy":  units = 1 if S >= K, else leverage
        side="sell": units = 1 if S <= K, else leverage

    Payoff: sum over observations of units * (S_obs - K) * sign
        where sign = +1 for buy, -1 for sell.

    Parameters
    ----------
    strike : float
        Fixed forward price for each periodic settlement. Must be positive.
    leverage : float
        Multiplier on accumulated units when price moves against the holder.
        Must be positive (typically > 1).
    side : str
        "buy" or "sell". Determines the direction of each periodic obligation.
    schedule : array-like of float
        Observation dates in years from trade inception.
    """

    def __init__(
        self, *, trade_id, maturity, notional, asset_indices,
        strike, leverage, side, schedule,
    ):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if strike <= 0:
            raise InstrumentError(f"strike must be positive, got {strike}")
        if leverage <= 0:
            raise InstrumentError(f"leverage must be positive, got {leverage}")
        if side not in ("buy", "sell"):
            raise InstrumentError(f"side must be 'buy' or 'sell', got '{side}'")
        self.strike = strike
        self.leverage = leverage
        self.side = side
        self.schedule = np.asarray(schedule)
        self._validate_schedule(self.schedule, maturity)

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self.schedule

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        obs_indices = self._resolve_obs_indices(
            self.schedule,
            n_steps,
            t_grid,
            include_past=False,
        )

        sign = 1.0 if self.side == "buy" else -1.0
        total_pnl = np.zeros(n_paths)

        for idx in obs_indices:
            s_obs = prices[:, idx]
            if self.side == "buy":
                units = np.where(s_obs >= self.strike, 1.0, self.leverage)
            else:
                units = np.where(s_obs <= self.strike, 1.0, self.leverage)
            total_pnl += units * (s_obs - self.strike) * sign

        return total_pnl
