import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class AsianOption(BaseInstrument):
    """Arithmetic average price/strike option.

    average_type="price" (fixed strike):
      Call: max(A - K, 0)   where A = mean(S(t_i)) over schedule
      Put:  max(K - A, 0)

    average_type="strike" (floating strike):
      Call: max(S(T) - A, 0)
      Put:  max(A - S(T), 0)
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices,
                 strike, option_type, average_type, schedule):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if option_type not in ("call", "put"):
            raise InstrumentError(f"option_type must be 'call' or 'put', got '{option_type}'")
        if average_type not in ("price", "strike"):
            raise InstrumentError(f"average_type must be 'price' or 'strike', got '{average_type}'")
        self.strike = strike
        self.option_type = option_type
        self.average_type = average_type
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
            obs_indices = np.searchsorted(t_grid, self.schedule, side="right") - 1
            obs_indices = np.clip(obs_indices, 0, n_steps - 1)
        else:
            t_grid_full = np.linspace(0.0, self.maturity, n_steps)
            obs_indices = np.searchsorted(t_grid_full, self.schedule, side="right") - 1
            obs_indices = np.clip(obs_indices, 1, n_steps - 1)

        avg = np.mean(prices[:, obs_indices], axis=1)

        if self.average_type == "price":
            if self.option_type == "call":
                return np.maximum(avg - self.strike, 0.0)
            else:
                return np.maximum(self.strike - avg, 0.0)
        else:  # strike
            s_terminal = prices[:, -1]
            if self.option_type == "call":
                return np.maximum(s_terminal - avg, 0.0)
            else:
                return np.maximum(avg - s_terminal, 0.0)
