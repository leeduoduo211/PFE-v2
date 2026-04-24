import numpy as np

from pfev2.utils.seeds import cantor_pair


class NumpyBackend:
    def randn(self, shape: tuple, seed: int) -> np.ndarray:
        rng = np.random.Generator(np.random.PCG64(seed))
        return rng.standard_normal(shape)

    def matmul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.matmul(a, b)

    def exp(self, x: np.ndarray) -> np.ndarray:
        return np.exp(x)

    def maximum(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.maximum(a, b)

    def derive_seed(self, base_seed: int, idx1: int, idx2: int) -> int:
        return base_seed + cantor_pair(idx1, idx2)
