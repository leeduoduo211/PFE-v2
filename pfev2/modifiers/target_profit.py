import numpy as np

from pfev2.modifiers.base import BaseModifier


class TargetProfit(BaseModifier):
    """Terminate trade when cumulative payoff hits target.

    Wraps any periodic instrument. With partial_fill=True (default), the
    payoff is capped at exactly the target. With partial_fill=False,
    the full raw payoff is returned even if it exceeds target.

    Design note: The ideal TargetProfit would hook into the inner instrument's
    per-period loop to stop accumulation early (like TARF does internally).
    However, the BaseModifier interface only sees the final aggregate payoff.
    The simple cap (np.minimum) is correct when the inner instrument's cumulative
    P&L is monotonically increasing. For scenarios where P&L oscillates, use
    the standalone TARF instrument instead.
    """

    def __init__(self, inner, target, partial_fill=True):
        super().__init__(inner)
        self.target = target
        self.partial_fill = partial_fill

    @property
    def requires_full_path(self) -> bool:
        return True

    def payoff(self, spots, path_history, t_grid=None):
        """Override payoff entirely — we need to cap the final result."""
        raw_payoff = self._inner.payoff(spots, path_history, t_grid)
        if self.partial_fill:
            return np.minimum(raw_payoff, self.target)
        else:
            # Overshoot allowed — return raw payoff unchanged
            return raw_payoff

    def _apply(self, raw_payoff, spots, path_history, t_grid=None):
        # Not used — payoff() is overridden directly
        return raw_payoff
