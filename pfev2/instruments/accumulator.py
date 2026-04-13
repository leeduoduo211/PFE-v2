import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class Accumulator(BaseInstrument):
    """
    Accumulator (side="buy") / Decumulator (side="sell").

    At each observation date, accumulates units:
    - Buy: 1 unit if S >= strike, leverage units if S < strike
    - Sell: 1 unit if S <= strike, leverage units if S > strike

    Payoff = sum over observations of: units * (S_obs - strike) * sign
    where sign = +1 for buy, -1 for sell.
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

    @property
    def requires_full_path(self) -> bool:
        return True

    def observation_dates(self) -> np.ndarray:
        return self.schedule

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        if t_grid is not None:
            # t_grid is relative to the current outer node: t_grid[-1] = remaining tau.
            # Convert absolute schedule dates to relative times: t_abs = maturity - tau.
            tau = float(t_grid[-1])
            t_abs = self.maturity - tau
            relative_schedule = self.schedule - t_abs
            # Keep only observations still in the remaining path (relative time > 0)
            future_mask = relative_schedule > 0.0
            obs_times = relative_schedule[future_mask]
            obs_indices = np.searchsorted(t_grid, obs_times, side="right") - 1
            obs_indices = np.clip(obs_indices, 0, n_steps - 1)
        else:
            t_grid_full = np.linspace(0.0, self.maturity, n_steps)
            obs_indices = np.searchsorted(t_grid_full, self.schedule, side="right") - 1
            obs_indices = np.clip(obs_indices, 1, n_steps - 1)

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
