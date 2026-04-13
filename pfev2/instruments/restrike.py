import numpy as np
from pfev2.instruments.base import BaseInstrument
from pfev2.core.exceptions import InstrumentError


class RestrikeOption(BaseInstrument):
    """
    Strike resets to S(reset_time). Payoff at maturity:
    - Call: max(S(T) - S(t_reset), 0)
    - Put:  max(S(t_reset) - S(T), 0)
    """

    def __init__(self, *, trade_id, maturity, notional, asset_indices, reset_time, option_type="call"):
        super().__init__(trade_id, maturity, notional, asset_indices)
        if reset_time <= 0 or reset_time >= maturity:
            raise InstrumentError(f"reset_time must be in (0, maturity), got {reset_time}")
        if option_type not in ("call", "put"):
            raise InstrumentError(f"option_type must be 'call' or 'put'")
        self.reset_time = reset_time
        self.option_type = option_type

    @property
    def requires_full_path(self) -> bool:
        return True

    def payoff(self, spots, path_history, t_grid=None):
        prices = path_history[:, :, 0]
        n_paths, n_steps = prices.shape

        if t_grid is not None:
            # t_grid is relative to the current outer node: t_grid[-1] = remaining tau.
            # Convert absolute reset_time to relative: t_abs = maturity - tau.
            tau = float(t_grid[-1])
            t_abs = self.maturity - tau
            relative_reset = self.reset_time - t_abs
            if relative_reset <= 0.0:
                # Strike-reset date has already passed; use the node spot (index 0)
                # as the best available proxy for S(reset_time).
                reset_idx = 0
            else:
                reset_idx = int(np.searchsorted(t_grid, relative_reset, side="right")) - 1
                reset_idx = max(0, min(reset_idx, n_steps - 2))
        else:
            t_grid_full = np.linspace(0.0, self.maturity, n_steps)
            reset_idx = int(np.searchsorted(t_grid_full, self.reset_time, side="right")) - 1
            reset_idx = max(1, min(reset_idx, n_steps - 2))

        s_reset = prices[:, reset_idx]
        s_terminal = prices[:, -1]

        if self.option_type == "call":
            return np.maximum(s_terminal - s_reset, 0.0)
        else:
            return np.maximum(s_reset - s_terminal, 0.0)
