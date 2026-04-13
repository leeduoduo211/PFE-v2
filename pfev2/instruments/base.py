from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from pfev2.core.exceptions import InstrumentError


class BaseInstrument(ABC):
    def __init__(
        self,
        trade_id: str,
        maturity: float,
        notional: float,
        asset_indices: tuple[int, ...],
    ):
        if maturity <= 0:
            raise InstrumentError(f"maturity must be positive, got {maturity}")
        if notional == 0:
            raise InstrumentError(f"notional must be non-zero, got {notional}")
        if not asset_indices:
            raise InstrumentError("asset_indices must not be empty")
        if len(asset_indices) > 5:
            raise InstrumentError(f"max 5 underlyings per trade, got {len(asset_indices)}")

        self.trade_id = trade_id
        self.maturity = maturity
        self.notional = notional
        self.asset_indices = tuple(asset_indices)

    @abstractmethod
    def payoff(
        self,
        spots: np.ndarray,
        path_history: np.ndarray | None,
        t_grid: np.ndarray | None = None,
    ) -> np.ndarray:
        ...

    @property
    def requires_full_path(self) -> bool:
        return False

    def is_alive(self, t: float) -> bool:
        return t < self.maturity

    def observation_dates(self) -> np.ndarray | None:
        return None
