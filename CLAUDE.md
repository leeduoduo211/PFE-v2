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

# Launch REST API (requires ".[api]" extra; interactive docs at /docs)
python3 -m uvicorn api.app:app --reload

# Launch React frontend (requires the API running; http://localhost:5173)
npm run dev --prefix frontend

# Frontend type-check + production build (what CI runs)
npm run build --prefix frontend

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

### REST API (`api/`)

FastAPI layer over the engine, the backend for the SPA frontend. `api/schemas.py` (Pydantic models mirroring the UI trade-spec dicts) → `api/app.py` (endpoints; validates synchronously via `ui/utils/converters.py`, returns specific 422s) → `api/jobs.py` (`RunStore`: in-process thread pool running `compute_pfe` with progress tracking) → `api/serializers.py` (registry and `PFEResult` → JSON) → `api/db.py` (SQLite persistence). Imports only Streamlit-free `ui.utils` modules (`converters`, `registry`, `t0_mtm`) — the API must not require streamlit. `api/schemas.py` deliberately uses `typing.List`/`Optional` (not PEP 604 unions) so pydantic can evaluate annotations on Python 3.9 dev machines; ruff per-file-ignores cover this.

**All routes are under `/api`** (so the SPA and API share one origin in the Docker image). Progress streams over SSE at `GET /api/runs/{id}/events` — the frontend consumes it with `EventSource` and closes on a terminal status. Persistence is opt-in via `PFEV2_DB_PATH` (env var); only terminal runs are persisted and reloaded on startup, and the MtM matrix is never persisted (so restored runs can't serve `?include_mtm=true`). Static SPA serving is opt-in via `PFEV2_STATIC_DIR` (the Docker image sets both). Tests pass an explicit `RunStore` so they don't touch the env-configured defaults.

### React frontend (`frontend/`)

Vite + React + TypeScript SPA over the REST API. `src/api/types.ts` mirrors `api/schemas.py` — app state IS the wire format, no mapping layer. `src/components/TradeForm.tsx` renders all instrument/modifier forms from `GET /api/registry` (same registry-driven pattern as the Streamlit trade builder); field types float/select/float_list/select_list/schedule/asset_select/asset_select_optional each have a renderer there. `src/styles/tokens.css` is the design system verbatim (source: `design/`); don't edit colors inline — use the CSS variables. Plotly is lazy-loaded via React.lazy in ResultsTab (bundle size). Run progress is consumed via `EventSource` on `/api/runs/{id}/events` in App.tsx (closed on terminal status to stop auto-reconnect). Dev proxy passes `/api/*` through unchanged to `127.0.0.1:8000` (no rewrite — the backend serves the `/api` prefix). CI type-checks and builds via `npm run build --prefix frontend`; the `docker` CI job builds the single-container image.

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
