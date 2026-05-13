import numpy as np


def cantor_pair(a: int, b: int) -> int:
    return (a + b) * (a + b + 1) // 2 + b


def derive_seed(base_seed: int, idx1: int, idx2: int) -> int:
    return base_seed + cantor_pair(idx1, idx2)


def make_inner_mc_seed_sequence(
    config_seed: int, t_idx: int, trade_idx: int
) -> np.random.SeedSequence:
    """Build a SeedSequence for an inner-MC pricing at (t_idx, trade_idx).

    The previous scheme summed two ``cantor_pair`` results — one over
    ``(0, t_idx)`` and one over ``(trade_idx, 0)`` — to derive an integer
    seed. That sum is **not** a bijection: ``(trade=2, t=0)`` and
    ``(trade=1, t=1)`` both produce the same offset, so two different
    inner MCs ran on identical random streams. The resulting spurious
    correlation biased exposure quantiles.

    ``SeedSequence`` mixes the entropy tuple through a cryptographic-
    quality hash, so distinct tuples produce statistically independent
    streams. Callers can ``.spawn()`` per-chunk child sequences for the
    chunked batch pricer.

    Parameters
    ----------
    config_seed : int
        User-supplied base seed from ``PFEConfig``.
    t_idx : int
        Outer time-step index.
    trade_idx : int
        Index of the trade in the portfolio.
    """
    return np.random.SeedSequence([int(config_seed), int(t_idx), int(trade_idx)])
