from pfev2.utils.seeds import cantor_pair, derive_seed


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
