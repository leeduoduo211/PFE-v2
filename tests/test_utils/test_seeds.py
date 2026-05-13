import numpy as np

from pfev2.utils.seeds import cantor_pair, derive_seed, make_inner_mc_seed_sequence


def test_cantor_pair_deterministic():
    assert cantor_pair(3, 7) == cantor_pair(3, 7)


def test_cantor_pair_unique():
    pairs = {cantor_pair(i, j) for i in range(10) for j in range(10)}
    assert len(pairs) == 100


def test_derive_seed_deterministic():
    s1 = derive_seed(42, 5, 10)
    s2 = derive_seed(42, 5, 10)
    assert s1 == s2


def test_derive_seed_varies():
    seeds = {derive_seed(42, i, j) for i in range(5) for j in range(5)}
    assert len(seeds) == 25


# ---------------------------------------------------------------------------
# Regression: the original PFE engine derived the inner-MC seed by summing
# two cantor_pair() results — one over (0, t_idx) and one over (trade_idx, 0).
# That sum is NOT a bijection: e.g. (trade=2, t=0) and (trade=1, t=1) both
# produce offset 3, so two different (trade, time) inner MCs ran on identical
# random streams, injecting spurious correlation into the MtM matrix and
# biasing exposure quantiles.
# ---------------------------------------------------------------------------


def test_make_inner_mc_seed_sequence_deterministic():
    s1 = make_inner_mc_seed_sequence(42, 3, 5)
    s2 = make_inner_mc_seed_sequence(42, 3, 5)
    # Same entropy -> same generated state (compare first spawned PCG64 state).
    rng1 = np.random.Generator(np.random.PCG64(s1))
    rng2 = np.random.Generator(np.random.PCG64(s2))
    np.testing.assert_array_equal(rng1.standard_normal(8), rng2.standard_normal(8))


def test_make_inner_mc_seed_sequence_no_collisions():
    """No two distinct (t_idx, trade_idx) pairs may share a seed sequence.

    Regression test: the previous cantor_pair-sum scheme collided
    (trade=2, t=0) with (trade=1, t=1), among many others.
    """
    streams = {}
    for t_idx in range(8):
        for trade_idx in range(8):
            seq = make_inner_mc_seed_sequence(42, t_idx, trade_idx)
            sample = tuple(np.random.Generator(np.random.PCG64(seq)).standard_normal(4))
            assert sample not in streams, (
                f"Seed collision: (t={t_idx}, trade={trade_idx}) shares a stream "
                f"with {streams[sample]}"
            )
            streams[sample] = (t_idx, trade_idx)


def test_make_inner_mc_seed_sequence_chunk_spawn_independent():
    """Chunks spawned from the same parent should produce distinct streams."""
    parent = make_inner_mc_seed_sequence(42, 0, 0)
    children = parent.spawn(4)
    samples = [
        tuple(np.random.Generator(np.random.PCG64(c)).standard_normal(4))
        for c in children
    ]
    assert len(set(samples)) == 4
