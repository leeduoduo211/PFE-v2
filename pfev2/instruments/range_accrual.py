import numpy as np

from pfev2.core.exceptions import InstrumentError
from pfev2.instruments.base import BaseInstrument


class RangeAccrual(BaseInstrument):
    """Pays proportional to fraction of observation dates spot stays in range.

    Payoff = (days_in_range / total_observations) * coupon_rate
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices,
                 lower, upper, coupon_rate, schedule):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if lower >= upper:
            raise InstrumentError(f"lower ({lower}) must be < upper ({upper})")
        self.lower = lower
        self.upper = upper
        self.coupon_rate = coupon_rate
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

        obs_indices = self._resolve_obs_indices(self.schedule, n_steps, t_grid)

        obs_prices = prices[:, obs_indices]
        in_range = (obs_prices >= self.lower) & (obs_prices <= self.upper)
        fraction = np.mean(in_range.astype(float), axis=1)
        return fraction * self.coupon_rate
