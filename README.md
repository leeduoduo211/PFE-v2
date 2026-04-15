# PFE-v2

A Python library for nested Monte Carlo Potential Future Exposure (PFE) calculation on light exotic derivatives. Supports FX and Equity asset classes with correlated multi-asset simulation.

## Installation

```bash
# Core library only
pip3 install -e .

# With Streamlit UI
pip3 install -e ".[ui]"

# With Numba JIT acceleration
pip3 install -e ".[numba]"

# All extras
pip3 install -e ".[ui,numba,plot,dev]"
```

**macOS system Python 3.9 workaround** (if editable install fails due to old pip):

```bash
echo "/path/to/PFE-v2" > $(python3 -c "import site; print(site.getusersitepackages())")/pfev2.pth
```

## Quick Start

```python
import numpy as np
from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import VanillaCall, WorstOfPut

market = MarketData(
    spots=np.array([100.0, 50.0]),
    vols=np.array([0.20, 0.30]),
    rates=np.array([0.05, 0.05]),
    domestic_rate=0.05,
    corr_matrix=np.array([[1.0, 0.5], [0.5, 1.0]]),
    asset_names=["AAPL", "XYZ"],
    asset_classes=["EQUITY", "EQUITY"],
)

portfolio = [
    VanillaCall(trade_id="C1", maturity=1.0, notional=100_000, asset_indices=(0,), strike=100.0),
    WorstOfPut(trade_id="WP1", maturity=1.0, notional=100_000, asset_indices=(0, 1), strikes=[100.0, 50.0]),
]

config = PFEConfig(n_outer=500, n_inner=500, seed=42, grid_frequency="monthly")
result = compute_pfe(portfolio, market, config)
print(result.summary())
```

## Streamlit UI

```bash
python3 -m streamlit run ui/app.py
```

Two modes available:
- **Wizard** — guided 4-step flow for building and running a portfolio
- **Dashboard** — single-page view for power users

## Instruments

**21 instrument types** across four categories (by pricing structure):

| Category | Instruments |
|---|---|
| European (terminal spot) | `VanillaCall`, `VanillaPut`, `Digital`, `ContingentOption`, `SingleBarrier` |
| Path-dependent (single asset) | `DoubleNoTouch`, `ForwardStartingOption`, `RestrikeOption`, `AsianOption`, `Cliquet`, `RangeAccrual` |
| Multi-asset | `WorstOfCall`, `WorstOfPut`, `BestOfCall`, `BestOfPut`, `DualDigital`, `TripleDigital` |
| Periodic (scheduled observation) | `Accumulator`, `Decumulator`, `Autocallable`, `TARF` |

**9 composable modifiers** in three groups:

| Group | Modifiers |
|---|---|
| Barrier (path-based kill/activate) | `KnockOut`, `KnockIn`, `RealizedVolKnockOut`, `RealizedVolKnockIn` |
| Payoff shaper | `PayoffCap`, `PayoffFloor`, `LeverageModifier` |
| Structural | `ObservationSchedule`, `TargetProfit` |

Barrier modifiers support three observation styles: **continuous** (every step), **discrete** (specific dates), and **window** (sub-period). `KnockOut` also supports a rebate payment on barrier breach.

See [`docs/product-catalog.md`](docs/product-catalog.md) for full product documentation including payoff formulas, use cases, PFE behavior, and worked examples.

## Configuration

Key `PFEConfig` parameters:

| Parameter | Default | Description |
|---|---|---|
| `n_outer` | 5000 | Outer MC paths (market scenarios) |
| `n_inner` | 2000 | Inner MC paths per node (re-pricing) |
| `confidence_level` | 0.95 | PFE percentile |
| `grid_frequency` | `"monthly"` | Time grid: `"daily"`, `"weekly"`, `"monthly"` |
| `margined` | `False` | Enable MPoR-based exposure |
| `mpor_days` | 10 | Margin period of risk (days) |
| `backend` | `"numpy"` | Compute backend: `"numpy"` or `"numba"` |

## Architecture

```
MarketData + TimeGrid + PFEConfig
    ↓
MultivariateGBM (outer paths, Cholesky decomp)
    ↓  for each (scenario, time step):
InnerMCPricer.price_trade() → MtM matrix
    ↓
Exposure = max(MtM, 0)  [or MPoR-adjusted if margined]
    ↓
PFE  = quantile(95%)
EPE  = mean(Exposure)
EEPE = Basel III effective EPE
```

The outer loop drives market scenario generation; each node is re-priced with a fresh inner MC to produce a mark-to-market distribution. Exposure is the positive part of MtM (counterparty credit perspective). Correlation across assets is handled via Cholesky decomposition of the input correlation matrix.

**Bottleneck**: the `n_outer × T_steps` Python loop in the risk calculator. At production scale (n_outer=5000, T=52 weekly steps, n_inner=2000) this is ~260K inner pricer calls. Enable the `numba` backend or refer to source comments for `ThreadPoolExecutor` / JAX parallelization hooks.

## Examples

| File | Description |
|---|---|
| `examples/basic_pfe.py` | 2-asset equity portfolio |
| `examples/fx_accumulator.py` | FX accumulator with KnockOut modifier, margined exposure |
| `examples/multi_asset_worst_of.py` | 3-asset portfolio with capped worst-of put |

```bash
python3 examples/basic_pfe.py
python3 examples/fx_accumulator.py
python3 examples/multi_asset_worst_of.py
```

## Tests

```bash
python3 -m pytest tests/ -v
```

236 tests covering core types, instruments, modifiers, engine, pricing, risk, and UI converters.

## Tech Stack

- Python 3.9+
- NumPy (required)
- Numba (optional — JIT acceleration)
- Streamlit + Plotly (optional — UI)
- matplotlib (optional — static plots)
