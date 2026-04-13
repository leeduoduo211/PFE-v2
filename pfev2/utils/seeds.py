def cantor_pair(a: int, b: int) -> int:
    return (a + b) * (a + b + 1) // 2 + b


def derive_seed(base_seed: int, idx1: int, idx2: int) -> int:
    return base_seed + cantor_pair(idx1, idx2)
