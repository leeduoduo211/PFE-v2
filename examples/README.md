# Examples

Three self-contained scripts that exercise the engine end-to-end. Each one
builds a market + portfolio, runs `compute_pfe()`, and prints the result
summary. They're the fastest way to see the library in action without the
Streamlit UI.

| Script | Scenario | Highlights |
|---|---|---|
| [`basic_pfe.py`](basic_pfe.py) | 2-asset equity portfolio (AAPL + XYZ) with a vanilla call and a worst-of put | Baseline: monthly grid, 500×500 paths, smooth profile |
| [`fx_accumulator.py`](fx_accumulator.py) | EURUSD monthly accumulator with up-and-out knock-out and margined exposure | FX asset class (foreign/domestic rate separation), knock-out modifier, MPoR |
| [`multi_asset_worst_of.py`](multi_asset_worst_of.py) | 3-asset equity basket with capped worst-of put + best-of call + short vanilla hedge | Modifier chaining (PayoffCap), short via negative notional, `per_trade_detail` |

## Run them

```bash
python3 examples/basic_pfe.py
python3 examples/fx_accumulator.py
python3 examples/multi_asset_worst_of.py
```

If you hit `ImportError: cannot import name 'VanillaOption'` it's almost
certainly because an older copy of `pfev2` is installed via `pip -e`.
Fix: `pip3 uninstall pfev2` then re-run from the repo root.

## Building your own

The minimum skeleton:

```python
import numpy as np
from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import VanillaOption

market = MarketData(
    spots=np.array([100.0]),
    vols=np.array([0.20]),
    rates=np.array([0.05]),
    domestic_rate=0.05,
    corr_matrix=np.array([[1.0]]),
    asset_names=["AAPL"],
    asset_classes=["EQUITY"],
)
portfolio = [
    VanillaOption(
        trade_id="C1", maturity=1.0, notional=100_000,
        asset_indices=(0,), strike=100.0, option_type="call",
    ),
]
config = PFEConfig(n_outer=500, n_inner=500, seed=42, grid_frequency="monthly")
result = compute_pfe(portfolio, market, config)
print(result.summary())
```

See the [wiki](https://github.com/leeduoduo211/PFE-v2/wiki) for the full
instrument catalogue and modifier reference.
