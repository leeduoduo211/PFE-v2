from __future__ import annotations

from abc import abstractmethod

import numpy as np


class BaseModifier:
    """Wraps an instrument, delegating attributes and transforming payoff."""

    def __init__(self, inner, **kwargs):
        self._inner = inner

    @property
    def trade_id(self):
        return self._inner.trade_id

    @property
    def maturity(self):
        return self._inner.maturity

    @property
    def notional(self):
        return self._inner.notional

    @property
    def asset_indices(self):
        return self._inner.asset_indices

    @property
    def requires_full_path(self) -> bool:
        return True

    def is_alive(self, t: float) -> bool:
        return self._inner.is_alive(t)

    def observation_dates(self) -> np.ndarray | None:
        return self._inner.observation_dates()

    def payoff(self, spots, path_history, t_grid=None):
        raw_payoff = self._inner.payoff(spots, path_history, t_grid)
        return self._apply(raw_payoff, spots, path_history)

    @abstractmethod
    def _apply(self, raw_payoff, spots, path_history) -> np.ndarray:
        ...
