import numpy as np
from pfev2.engine.backends.numpy_backend import NumpyBackend


def test_randn_shape():
    backend = NumpyBackend()
    z = backend.randn((100, 10, 3), seed=42)
    assert z.shape == (100, 10, 3)


def test_randn_deterministic():
    backend = NumpyBackend()
    z1 = backend.randn((50, 5, 2), seed=123)
    z2 = backend.randn((50, 5, 2), seed=123)
    np.testing.assert_array_equal(z1, z2)


def test_randn_different_seeds():
    backend = NumpyBackend()
    z1 = backend.randn((50, 5, 2), seed=1)
    z2 = backend.randn((50, 5, 2), seed=2)
    assert not np.allclose(z1, z2)


def test_matmul():
    backend = NumpyBackend()
    a = np.random.randn(100, 3, 4)
    b = np.random.randn(4, 2)
    result = backend.matmul(a, b)
    expected = a @ b
    np.testing.assert_allclose(result, expected)


def test_exp():
    backend = NumpyBackend()
    x = np.array([0.0, 1.0, -1.0])
    np.testing.assert_allclose(backend.exp(x), np.exp(x))


def test_maximum():
    backend = NumpyBackend()
    a = np.array([-1.0, 2.0, -3.0])
    b = np.array([0.0, 0.0, 0.0])
    np.testing.assert_array_equal(backend.maximum(a, b), [0.0, 2.0, 0.0])


def test_derive_seed():
    backend = NumpyBackend()
    s1 = backend.derive_seed(42, 3, 7)
    s2 = backend.derive_seed(42, 3, 7)
    assert s1 == s2
    assert s1 != backend.derive_seed(42, 3, 8)
