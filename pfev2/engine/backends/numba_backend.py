import numpy as np

from pfev2.utils.seeds import cantor_pair

try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False


if HAS_NUMBA:
    @njit(cache=True, parallel=True)
    def _randn_parallel(n_paths, n_steps, n_assets, seed):
        result = np.empty((n_paths, n_steps, n_assets))
        for p in prange(n_paths):
            path_seed = seed + p * 1000003
            np.random.seed(path_seed)
            for t in range(n_steps):
                for a in range(n_assets):
                    result[p, t, a] = np.random.randn()
        return result


class NumbaBackend:
    def __init__(self):
        if not HAS_NUMBA:
            raise ImportError("numba >= 0.59 required for NumbaBackend")

    def randn(self, shape: tuple, seed: int) -> np.ndarray:
        if len(shape) == 3:
            return _randn_parallel(shape[0], shape[1], shape[2], seed)
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
