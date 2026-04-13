from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Instrument(Protocol):
    trade_id: str
    maturity: float
    notional: float
    asset_indices: tuple[int, ...]

    def payoff(self, spots: np.ndarray, path_history: np.ndarray | None) -> np.ndarray: ...

    @property
    def requires_full_path(self) -> bool: ...

    def is_alive(self, t: float) -> bool: ...

    def observation_dates(self) -> np.ndarray | None: ...


@runtime_checkable
class SimulationBackend(Protocol):
    def randn(self, shape: tuple, seed: int) -> np.ndarray: ...
    def matmul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray: ...
    def exp(self, x: np.ndarray) -> np.ndarray: ...
    def maximum(self, a: np.ndarray, b: np.ndarray) -> np.ndarray: ...
    def derive_seed(self, base_seed: int, idx1: int, idx2: int) -> int: ...
