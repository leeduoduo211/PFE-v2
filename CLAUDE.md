# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, core only)
pip3 install -e .

# Install with all extras
pip3 install -e ".[ui,numba,plot,dev]"

# Run tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_instruments/test_vanilla.py -v

# Run a single test
python3 -m pytest tests/test_ui/test_registry.py::TestInstrumentRegistry::test_vanilla_option_spec -v

# Launch Streamlit UI
python3 -m streamlit run ui/app.py

# Quick import sanity check
python3 -c "from pfev2 import compute_pfe; print('OK')"
```

Always use `python3` and `pip3`, never `python` or `pip`.

## Architecture

### Core Library (`pfev2/`)

Nested Monte Carlo PFE engine. The computation pipeline:

```
MarketData + PFEConfig → TimeGrid → MultivariateGBM (outer paths, Cholesky)
    → for each (scenario, time_step): InnerMCPricer.price_trade() → MtM matrix
    → Exposure = max(MtM, 0) → PFE = quantile(95%), EPE = mean, EEPE = effective EPE
```

Key entry point: `pfev2.risk.pfe.compute_pfe(portfolio, market, config)` returns `PFEResult`.

**Instruments** (`pfev2/instruments/`): 18 types inheriting from `BaseInstrument`. Each implements `payoff(spots_terminal, path_history) -> np.ndarray`. Four categories: European (terminal spot), Path-dependent (single asset, full path), Multi-asset (multiple underlyings), Periodic (scheduled observation). Unified option classes use `option_type="call"|"put"` parameter (`VanillaOption`, `WorstOfOption`, `BestOfOption`). `AccumulatorDecumulator` uses `side="buy"|"sell"`. `Dispersion` trades index vol vs component vols.

**Modifiers** (`pfev2/modifiers/`): 9 types inheriting from `BaseModifier`. Decorator pattern wrapping instruments. `_apply(raw_payoff, spots, path_history, t_grid)` transforms the payoff. Barrier modifiers support three observation styles: continuous, discrete, window.

**Engine** (`pfev2/engine/`): `MultivariateGBM` generates correlated paths via Cholesky decomposition. Backends: `numpy` (default) and `numba` (optional JIT).

### Streamlit UI (`ui/`)

Tab-based layout: Market Data → Portfolio → Configuration → Results.

**Data flow**: `registry.py` defines what fields exist per product → `product_content.py` defines how to group/label/describe them → `trade_builder.py` renders editable forms → `term_sheet.py` renders read-only views → `trade_economics.py` provides term-sheet text and scenarios → `payoff_display.py` provides formula strings and sparklines.

**Registry pattern**: `INSTRUMENT_REGISTRY` (18 entries) and `MODIFIER_REGISTRY` (9 entries) drive dynamic UI form generation. Each entry maps a type key to `{cls, label, category, n_assets, fields}`. Adding a new instrument requires entries in: the registry, `product_content.py` (sections, description, scenarios), `trade_economics.py` (term-sheet text builder), and `payoff_display.py` (formula string).

**Session state**: `ui/utils/session.py` manages `market`, `portfolio`, `config`, `runs` in `st.session_state`. `ui/utils/converters.py` bridges UI spec dicts to `pfev2` instrument objects.

## Key Patterns

- Instruments use `asset_indices: tuple[int, ...]` (indices into global asset array), not asset names. The UI layer maps names to indices via `converters.py`.
- `payoff_sparkline()` returns `Optional[go.Figure]` — returns `None` for complex path-dependent types (AsianOption, Cliquet, RangeAccrual, Autocallable, TARF). Callers must handle `None`.
- Trade specs in the UI are dicts: `{trade_id, instrument_type, direction, params, modifiers}`. This is the universal format passed between builder, portfolio table, term sheet, and converters.
- The `seed_builder_from_trade()` function in `trade_builder.py` pre-seeds Streamlit widget state using `{key_prefix}_inst_{field_name}` keys. Any changes to field rendering must preserve this key pattern.
- `BaseInstrument.__init__` enforces max 5 underlyings per trade (`len(asset_indices) > 5` raises `InstrumentError`).
- Direction (long/short) is applied via notional negation in `converters.py`, not in instrument classes. `direction="short"` → `notional = -notional`.
- Registry field schema uses `"choices"` for select/select_list options (NOT `"options"`). Every field entry includes `"name"`, `"type"`, `"label"`, `"default"`, `"help"`. For variable-asset-count instruments, `float_list` and `select_list` defaults must be lists matching minimum `n_assets` (e.g., `"default": [100.0, 100.0]` for `"n_assets": "2-5"`).
- `BestOfOption` put payoff is asymmetric: `max_i(max(1 - S_i/K_i, 0))` — evaluates individual puts first, then takes maximum. This differs from the call pattern and must be preserved in any refactoring.
