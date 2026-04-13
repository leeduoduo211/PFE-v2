"""
Market data snapshot save/load utilities.

Provides serialize/deserialize/validate functions for persisting a market data
state dict as JSON. The envelope schema is versioned (version=1) so future
breaking changes can be detected gracefully.
"""

import json
from typing import Any

import numpy as np

_REQUIRED_FIELDS = [
    "asset_names",
    "asset_classes",
    "spots",
    "vols",
    "rates",
    "domestic_rate",
    "corr_matrix",
]

_ARRAY_FIELDS = ["asset_names", "asset_classes", "spots", "vols", "rates"]


def _to_python(obj: Any) -> Any:
    """Recursively convert numpy scalars/arrays to plain Python types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, list):
        return [_to_python(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_python(v) for k, v in obj.items()}
    return obj


def serialize_snapshot(state: dict, name: str = "") -> str:
    """Serialize a market data state dict to a JSON string.

    Parameters
    ----------
    state:
        Dict containing market data fields (spots, vols, corr_matrix, etc.).
        Values may be plain Python lists or numpy arrays.
    name:
        Optional human-readable label stored in the envelope.

    Returns
    -------
    str
        JSON string with version envelope.
    """
    envelope = {
        "version": 1,
        "name": name,
    }
    for field in _REQUIRED_FIELDS:
        if field in state:
            envelope[field] = _to_python(state[field])

    # Carry through any extra fields present in state
    for key, value in state.items():
        if key not in envelope:
            envelope[key] = _to_python(value)

    return json.dumps(envelope)


def deserialize_snapshot(json_str: str) -> dict:
    """Parse a JSON snapshot string and return the market data dict.

    The version/name envelope keys are stripped; the caller receives only the
    market data fields.

    Parameters
    ----------
    json_str:
        JSON string produced by :func:`serialize_snapshot`.

    Returns
    -------
    dict
        Market data dict (no version or name keys).
    """
    envelope = json.loads(json_str)
    # Strip envelope-only keys; keep everything else as market data
    state = {k: v for k, v in envelope.items() if k not in ("version", "name")}
    return state


def validate_snapshot(data: dict) -> list:
    """Validate a snapshot dict (envelope or deserialized) for consistency.

    Checks:
    - All required fields are present.
    - asset_names, asset_classes, spots, vols, rates all have the same length.
    - corr_matrix is an N×N square matching that length.

    Parameters
    ----------
    data:
        Dict to validate. May include version/name envelope keys.

    Returns
    -------
    list[str]
        Empty list if valid; otherwise a list of human-readable error strings.
    """
    errors: list = []

    # 1. Required field presence
    for field in _REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        # Cannot do length checks without the fields
        return errors

    # 2. Array length consistency
    lengths = {field: len(data[field]) for field in _ARRAY_FIELDS}
    unique_lengths = set(lengths.values())
    if len(unique_lengths) > 1:
        detail = ", ".join(f"{f}={l}" for f, l in lengths.items())
        errors.append(f"Length mismatch among array fields: {detail}")

    # 3. Correlation matrix shape
    n = lengths["asset_names"]
    corr = data["corr_matrix"]
    if len(corr) != n:
        errors.append(
            f"corr_matrix row count {len(corr)} does not match asset count {n}"
        )
    else:
        bad_rows = [i for i, row in enumerate(corr) if len(row) != n]
        if bad_rows:
            errors.append(
                f"corr_matrix is not square (N={n}); bad rows: {bad_rows}"
            )

    return errors
