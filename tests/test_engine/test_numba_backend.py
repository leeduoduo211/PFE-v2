import numpy as np
import pytest

try:
    from pfev2.engine.backends.numba_backend import NumbaBackend, HAS_NUMBA
except ImportError:
    HAS_NUMBA = False

pytestmark = pytest.mark.skipif(not HAS_NUMBA, reason="numba not installed")


def test_randn_shape():
    backend = NumbaBackend()
    z = backend.randn((100, 10, 3), seed=42)
    assert z.shape == (100, 10, 3)


def test_randn_deterministic():
    backend = NumbaBackend()
    z1 = backend.randn((50, 5, 2), seed=123)
    z2 = backend.randn((50, 5, 2), seed=123)
    np.testing.assert_array_equal(z1, z2)


def test_matmul():
    backend = NumbaBackend()
    a = np.random.randn(100, 3, 4)
    b = np.random.randn(4, 2)
    result = backend.matmul(a, b)
    expected = a @ b
    np.testing.assert_allclose(result, expected, rtol=1e-10)


def test_matches_numpy_backend():
    from pfev2.engine.backends.numpy_backend import NumpyBackend
    nb = NumbaBackend()
    npb = NumpyBackend()
    z_nb = nb.randn((100, 10, 3), seed=42)
    z_np = npb.randn((100, 10, 3), seed=42)
    assert z_nb.shape == z_np.shape
    np.testing.assert_allclose(z_nb.mean(), 0.0, atol=0.1)
    np.testing.assert_allclose(z_nb.std(), 1.0, atol=0.1)
