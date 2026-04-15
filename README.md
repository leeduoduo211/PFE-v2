# PFE-v2

A Python library for computing **Potential Future Exposure (PFE)** on light exotic derivatives using nested Monte Carlo simulation. Supports FX and Equity asset classes with correlated multi-asset paths.

## What is PFE?

**Potential Future Exposure** measures the maximum expected credit exposure at a future date at a given confidence level (typically 95th percentile). It answers: *"What is the worst-case mark-to-market value of this derivatives portfolio over its lifetime?"*

PFE is a core input for:
- **Counterparty credit risk** capital calculations (SA-CCR, IMM)
- **Credit Value Adjustment (CVA)** pricing
- **Credit limit monitoring** and pre-deal checking
- **Margin period of risk (MPoR)** based exposure for margined portfolios

```
               Exposure
                  ^
                  |        ╭──╮     ╭──────╮
     Peak PFE ----+-------╱----╲---╱--------╲-----------
                  |      ╱      ╲ ╱          ╲
          EPE ----+-----/--------X-------------\--------
                  |    /        ╱ ╲             ╲
                  |   ╱       ╱    ╲              ╲
                  |  ╱      ╱       ╲               ╲
                  | ╱     ╱          ╲                ╲
                  +╱────╱─────────────╲─────────────────╲──> Time
                  0    3m    6m       9m     12m
                       
                  ── PFE (95th percentile)
                  ── EPE (expected positive exposure)
```

## How It Works

PFE-v2 uses a **nested Monte Carlo** approach — an outer simulation generates future market scenarios, and at each scenario node an inner simulation re-prices every trade in the portfolio:

```
                    ┌─────────────────────────┐
                    │  MarketData + PFEConfig  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   MultivariateGBM        │
                    │   (Outer MC simulation)  │
                    │                          │
                    │   n_outer paths           │
                    │   × T time steps          │
                    │   × n_assets              │
                    │                          │
                    │   Correlated via          │
                    │   Cholesky decomposition  │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
     ┌────────▼───────┐ ┌───────▼────────┐ ┌───────▼────────┐
     │  Scenario 1     │ │  Scenario 2     │ │  Scenario N     │
     │  Time step t    │ │  Time step t    │ │  Time step t    │
     └────────┬───────┘ └───────┬────────┘ └───────┬────────┘
              │                  │                   │
     ┌────────▼───────┐ ┌───────▼────────┐ ┌───────▼────────┐
     │  InnerMCPricer  │ │  InnerMCPricer  │ │  InnerMCPricer  │
     │  n_inner paths  │ │  n_inner paths  │ │  n_inner paths  │
     │  → MtM value    │ │  → MtM value    │ │  → MtM value    │
     └────────┬───────┘ └───────┬────────┘ └───────┬────────┘
              │                  │                   │
              └──────────────────┼──────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Exposure Aggregation    │
                    │                          │
                    │  Exposure = max(MtM, 0)  │
                    │  PFE  = quantile(95%)    │
                    │  EPE  = mean(Exposure)   │
                    │  EEPE = effective EPE    │
                    └─────────────────────────┘
```

The outer loop drives market scenario generation; each node is re-priced with a fresh inner MC to produce a mark-to-market distribution. Exposure is the positive part of MtM (counterparty credit risk perspective). Correlation across assets is handled via Cholesky decomposition of the input correlation matrix.

## Installation

```bash
# Core library only
pip3 install -e .

# With Streamlit UI
pip3 install -e ".[ui]"

# With Numba JIT acceleration
pip3 install -e ".[numba]"

# All extras (UI + Numba + plotting + dev tools)
pip3 install -e ".[ui,numba,plot,dev]"
```

**Requirements:** Python 3.9+, NumPy

## Quick Start

```python
import numpy as np
from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import VanillaOption, WorstOfOption

# Define market: 2 correlated equity assets
market = MarketData(
    spots=np.array([100.0, 50.0]),
    vols=np.array([0.20, 0.30]),
    rates=np.array([0.05, 0.05]),
    domestic_rate=0.05,
    corr_matrix=np.array([[1.0, 0.5], [0.5, 1.0]]),
    asset_names=["AAPL", "XYZ"],
    asset_classes=["EQUITY", "EQUITY"],
)

# Build portfolio: a vanilla call + a worst-of put
portfolio = [
    VanillaOption(
        trade_id="C1", maturity=1.0, notional=100_000,
        asset_indices=(0,), strike=100.0, option_type="call",
    ),
    WorstOfOption(
        trade_id="WP1", maturity=1.0, notional=100_000,
        asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put",
    ),
]

# Run PFE calculation
config = PFEConfig(n_outer=500, n_inner=500, seed=42, grid_frequency="monthly")
result = compute_pfe(portfolio, market, config)
print(result.summary())
```

**Output:**

```
Peak PFE:          3,936,197.30
EEPE:              1,055,839.29
Confidence:        95%
Outer paths:       500
Inner paths:       500
Margined:          False
Horizon:           12 months
Computation time:  0.2s
```

## Instruments

**18 instrument types** across four categories, organized by how they are priced:

### European (terminal spot only)

These instruments depend only on the spot price at maturity — no path history needed.

| Instrument | Description | Assets |
|---|---|---|
| `VanillaOption` | Standard call/put, `max(S-K, 0)` or `max(K-S, 0)` | 1 |
| `Digital` | Binary payout if spot crosses strike | 1 |
| `ContingentOption` | Pays vanilla payoff on asset A only if asset B crosses a trigger | 2 |
| `SingleBarrier` | European with up/down knock-in/out at a single level | 1 |

### Path-dependent (single asset, full path)

These instruments observe the entire price path — the engine passes full simulation history.

| Instrument | Description | Assets |
|---|---|---|
| `DoubleNoTouch` | Pays fixed amount if spot stays within two barriers over life | 1 |
| `ForwardStartingOption` | Strike set as % of spot at a future date | 1 |
| `RestrikeOption` | Strike resets to spot at observation date if favorable | 1 |
| `AsianOption` | Payoff on arithmetic average price over observation dates | 1 |
| `Cliquet` | Sum of capped/floored periodic returns | 1 |
| `RangeAccrual` | Accrues coupon for each day spot is within a range | 1 |

### Multi-asset (multiple underlyings)

These instruments reference 2-5 correlated assets simultaneously.

| Instrument | Description | Assets |
|---|---|---|
| `WorstOfOption` | Call/put driven by the worst-performing asset | 2-5 |
| `BestOfOption` | Call/put driven by the best-performing asset | 2-5 |
| `Dispersion` | Long component vols, short basket vol — captures correlation | 2-5 |
| `DualDigital` | Binary payout if both assets cross their respective strikes | 2 |
| `TripleDigital` | Binary payout if all three assets cross strikes | 3 |

### Periodic (scheduled observation)

These instruments observe prices at discrete dates and accumulate payoffs over time.

| Instrument | Description | Assets |
|---|---|---|
| `Accumulator` | Accumulate/decumulate units at a strike on each observation date, with leverage | 1 |
| `Autocallable` | Periodically checks if spot exceeds barrier; auto-redeems with coupon if triggered | 1-5 |
| `TARF` | Target Accrual Redemption Forward — accumulates until a profit target is hit | 1 |

## Modifiers

**9 composable modifiers** that wrap any instrument using the decorator pattern. Modifiers chain — e.g., `PayoffCap(KnockOut(VanillaOption(...)))`.

```python
from pfev2.instruments import VanillaOption
from pfev2.modifiers import KnockOut, PayoffCap

# A vanilla call that knocks out at 130 and is capped at 20% payoff
trade = PayoffCap(
    KnockOut(
        VanillaOption(trade_id="T1", maturity=1.0, notional=100_000,
                      asset_indices=(0,), strike=100.0, option_type="call"),
        barrier=130.0, direction="up",
    ),
    cap=0.2,
)
```

| Group | Modifiers | Description |
|---|---|---|
| **Barrier** | `KnockOut`, `KnockIn`, `RealizedVolKnockOut`, `RealizedVolKnockIn` | Kill or activate the trade when spot (or realized vol) crosses a barrier. Three observation styles: continuous, discrete, window. `KnockOut` supports a rebate on breach. |
| **Payoff shaper** | `PayoffCap`, `PayoffFloor`, `LeverageModifier` | Cap, floor, or scale the final payoff |
| **Structural** | `ObservationSchedule`, `TargetProfit` | Control when the trade observes prices, or auto-terminate at a profit target |

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `n_outer` | 5000 | Outer MC paths (market scenarios) |
| `n_inner` | 2000 | Inner MC paths per node (re-pricing) |
| `confidence_level` | 0.95 | PFE percentile |
| `grid_frequency` | `"monthly"` | Time grid: `"daily"`, `"weekly"`, `"monthly"` |
| `margined` | `False` | Enable margin period of risk (MPoR) based exposure |
| `mpor_days` | 10 | Margin period of risk in business days |
| `backend` | `"numpy"` | Compute backend: `"numpy"` or `"numba"` |
| `seed` | `None` | Random seed for reproducibility |

**Performance note:** The computational bottleneck is `n_outer x T_steps` inner pricer calls. At production scale (n_outer=5000, T=52 weekly steps, n_inner=2000) this is ~260K inner MC invocations. European instruments are vectorized across all outer paths; path-dependent instruments fall back to per-path loops. Enable `numba` backend for JIT acceleration on large runs.

## Streamlit UI

```bash
python3 -m streamlit run ui/app.py
```

Two modes:
- **Wizard** — guided 4-step flow: Market Data -> Portfolio -> Configuration -> Results
- **Dashboard** — single-page view for power users

The UI is driven by a registry pattern — adding a new instrument type to the registry automatically generates the trade builder form, term sheet, and payoff display.

## Examples

| File | What it demonstrates |
|---|---|
| [`examples/basic_pfe.py`](examples/basic_pfe.py) | 2-asset equity portfolio (vanilla call + worst-of put) |
| [`examples/fx_accumulator.py`](examples/fx_accumulator.py) | FX accumulator with KnockOut modifier, margined exposure |
| [`examples/multi_asset_worst_of.py`](examples/multi_asset_worst_of.py) | 3-asset portfolio with capped worst-of put, best-of call, and vanilla hedge |

```bash
python3 examples/basic_pfe.py
python3 examples/fx_accumulator.py
python3 examples/multi_asset_worst_of.py
```

## Project Structure

```
pfev2/
  core/           # Types (MarketData, PFEConfig), exceptions
  engine/         # MultivariateGBM, Cholesky, simulation backends (numpy/numba)
  instruments/    # 18 instrument classes (BaseInstrument ABC)
  modifiers/      # 9 modifier classes (BaseModifier, decorator pattern)
  pricing/        # InnerMCPricer — re-pricing engine at each scenario node
  risk/           # compute_pfe() entry point, PFEResult, exposure aggregation
  utils/          # Seed generation (Cantor pairing), helpers

ui/               # Streamlit UI (registry-driven, wizard + dashboard modes)
tests/            # 310 tests across instruments, modifiers, engine, risk, UI
examples/         # Runnable example scripts
docs/             # Product catalog with payoff formulas and use cases
```

## Tests

```bash
python3 -m pytest tests/ -v
```

310 tests covering core types, instruments, modifiers, engine, pricing, risk, and UI converters.

## Tech Stack

- **Python 3.9+** (core)
- **NumPy** (required — all simulation and payoff computation)
- **Numba** (optional — JIT acceleration for the simulation backend)
- **Streamlit + Plotly** (optional — interactive UI)
- **matplotlib** (optional — static plotting)

## License

MIT
