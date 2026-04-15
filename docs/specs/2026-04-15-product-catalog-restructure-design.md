# Product Catalog Restructure — Design Spec

**Date:** 2026-04-15
**Scope:** Taxonomy, documentation, and coverage for PFE-v2 instruments and modifiers

---

## 1. Goals

1. **Re-categorize** all instruments and modifiers by underlying pricing structure
2. **Document** every product with a full product guide (payoff formula, use case, PFE behavior, risk characteristics, worked example)
3. **Add 6 new instruments** and **1 new modifier**, plus **enhance 4 existing barrier modifiers** with observation styles and rebate

## 2. Instrument Taxonomy

Four categories based on how the payoff is computed:

### Category 1 — European (terminal spot only)

Payoff depends only on spot(s) at maturity. `requires_full_path = False`.

| Product | Status | Assets | Module |
|---|---|---|---|
| VanillaCall | existing | 1 | `vanilla.py` |
| VanillaPut | existing | 1 | `vanilla.py` |
| Digital | existing | 1 | `digital.py` |
| ContingentOption | existing | 2 | `contingent.py` |
| SingleBarrier | **new** | 1 | `single_barrier.py` |

### Category 2 — Path-dependent (single asset, full path)

Payoff depends on the price path. `requires_full_path = True`.

| Product | Status | Assets | Module |
|---|---|---|---|
| DoubleNoTouch | existing | 1 | `barrier.py` |
| ForwardStartingOption | existing | 1 | `forward_starting.py` |
| RestrikeOption | existing | 1 | `restrike.py` |
| AsianOption | **new** | 1 | `asian.py` |
| Cliquet | **new** | 1 | `cliquet.py` |
| RangeAccrual | **new** | 1 | `range_accrual.py` |

### Category 3 — Multi-asset (multiple underlyings)

Payoff depends on relative performance across assets.

| Product | Status | Assets | Module |
|---|---|---|---|
| WorstOfCall | existing | 2-5 | `worst_best_of.py` |
| WorstOfPut | existing | 2-5 | `worst_best_of.py` |
| BestOfCall | existing | 2-5 | `worst_best_of.py` |
| BestOfPut | existing | 2-5 | `worst_best_of.py` |
| DualDigital | existing | 2 | `digital.py` |
| TripleDigital | existing | 3 | `digital.py` |

### Category 4 — Periodic observation (scheduled path)

Payoff accumulates across discrete observation dates. `requires_full_path = True` + `observation_dates()` returns a schedule.

| Product | Status | Assets | Module |
|---|---|---|---|
| Accumulator / Decumulator | existing | 1 | `accumulator.py` |
| Autocallable | **new** | 1-5 | `autocallable.py` |
| TARF | **new** | 1 | `tarf.py` |

## 3. Modifier Taxonomy

Three groups based on what they transform:

### Group A — Barrier modifiers (path-based kill/activate)

Transform payoff to zero or pass-through based on path behavior. All barrier modifiers support three observation styles:

- **Continuous** (default): checked at every simulation step
- **Discrete**: checked only on specified observation dates
- **Window**: checked continuously but only during `[window_start, window_end]`

| Modifier | Status | New parameters |
|---|---|---|
| KnockOut | existing, **enhanced** | `observation_style`, `observation_dates`, `window_start`, `window_end`, `rebate` |
| KnockIn | existing, **enhanced** | `observation_style`, `observation_dates`, `window_start`, `window_end` |
| RealizedVolKnockOut | existing, **enhanced** | `observation_style`, `observation_dates`, `window_start`, `window_end` |
| RealizedVolKnockIn | existing, **enhanced** | `observation_style`, `observation_dates`, `window_start`, `window_end` |

### Group B — Payoff shapers (transform the raw payoff value)

| Modifier | Status |
|---|---|
| PayoffCap | existing, unchanged |
| PayoffFloor | existing, unchanged |
| LeverageModifier | existing, unchanged |

### Group C — Structural modifiers (change observation/termination mechanics)

| Modifier | Status |
|---|---|
| ObservationSchedule | existing, unchanged |
| TargetProfit | **new** |

### Modifier Compatibility Matrix

| Modifier | European | Path-dep | Multi-asset | Periodic |
|---|---|---|---|---|
| KnockOut / KnockIn | yes | yes | yes | yes |
| RealizedVol KO/KI | rare | yes | yes | yes |
| PayoffCap / Floor | yes | yes | yes | yes |
| LeverageModifier | yes | yes | yes | yes |
| ObservationSchedule | no | yes | no | built-in |
| TargetProfit | no | no | no | yes |

## 4. New Instrument Designs

### 4.1 SingleBarrier

European-style barrier checked at expiry only. Distinct from KnockOut/KnockIn modifiers (which monitor along the path).

**Payoff:**
```
barrier_type = "in":
  Call: max(S(T) - K, 0) * 1{barrier_condition_met}
  Put:  max(K - S(T), 0) * 1{barrier_condition_met}

barrier_type = "out":
  Call: max(S(T) - K, 0) * 1{barrier_condition_NOT_met}
  Put:  max(K - S(T), 0) * 1{barrier_condition_NOT_met}

where barrier_condition:
  direction = "up":  S(T) > barrier
  direction = "down": S(T) < barrier
```

**Constructor:**
```python
SingleBarrier(
    trade_id: str,
    maturity: float,
    notional: float,
    asset_indices: tuple[int, ...],
    strike: float,
    barrier: float,
    option_type: str,         # "call" / "put"
    barrier_direction: str,   # "up" / "down"
    barrier_type: str,        # "in" / "out"
)
```

`requires_full_path = False`. Category: European.

### 4.2 AsianOption

Arithmetic average price/strike option.

**Payoff:**
```
average_type = "price" (fixed strike):
  Call: max(A - K, 0)     where A = mean(S(t_i)) over schedule
  Put:  max(K - A, 0)

average_type = "strike" (floating strike):
  Call: max(S(T) - A, 0)
  Put:  max(A - S(T), 0)
```

**Constructor:**
```python
AsianOption(
    trade_id: str,
    maturity: float,
    notional: float,
    asset_indices: tuple[int, ...],
    strike: float,
    option_type: str,      # "call" / "put"
    average_type: str,     # "price" / "strike"
    schedule: list[float], # observation dates for averaging
)
```

`requires_full_path = True`. Category: Path-dependent.

### 4.3 Cliquet

Periodic reset option summing clipped local returns.

**Payoff:**
```
return_i = clip(S(t_i) / S(t_{i-1}) - 1, local_floor, local_cap)
Payoff = N * max(sum(return_i), global_floor)
```

**Constructor:**
```python
Cliquet(
    trade_id: str,
    maturity: float,
    notional: float,
    asset_indices: tuple[int, ...],
    local_cap: float,       # e.g. 0.05 (5% per period)
    local_floor: float,     # e.g. 0.0 (no negative returns)
    global_floor: float,    # e.g. 0.0 (minimum total payoff)
    schedule: list[float],  # reset dates
)
```

`requires_full_path = True`. Category: Path-dependent.

### 4.4 RangeAccrual

Pays proportional to time spot stays within a range.

**Payoff:**
```
Payoff = N * (days_in_range / total_observations) * coupon_rate
```

**Constructor:**
```python
RangeAccrual(
    trade_id: str,
    maturity: float,
    notional: float,
    asset_indices: tuple[int, ...],
    lower: float,           # range lower bound
    upper: float,           # range upper bound
    coupon_rate: float,     # e.g. 0.08 (8% annualized)
    schedule: list[float],  # observation dates
)
```

`requires_full_path = True`. Category: Path-dependent.

### 4.5 Autocallable

Early redemption if spot above trigger at observation dates. Put-like loss at maturity if never called.

**Payoff:**
```
At each observation t_i:
  if worst_performance(t_i) >= autocall_trigger:
    terminate, payoff = coupon_rate * i  (accrued coupon)

At maturity (if not called):
  if worst_performance(T) >= put_strike:
    payoff = 0  (principal returned, no loss)
  else:
    payoff = worst_performance(T) - 1.0  (negative, represents loss)
```

**Constructor:**
```python
Autocallable(
    trade_id: str,
    maturity: float,
    notional: float,
    asset_indices: tuple[int, ...],  # 1-5 assets
    autocall_trigger: float,  # e.g. 1.0 (100% of initial)
    coupon_rate: float,       # per-period coupon
    put_strike: float,        # downside barrier at maturity
    schedule: list[float],    # observation dates for autocall
)
```

For multi-asset: trigger based on worst-of performance across `asset_indices`.

`requires_full_path = True`. Category: Periodic.

### 4.6 TARF (Target Accrual Redemption Forward)

Accumulator that terminates when cumulative profit hits a target. Partial fill on the final fixing.

**Payoff:**
```
At each observation t_i (while cumulative < target):
  if side == "buy":
    units = 1 if S(t_i) >= K else leverage
    period_pnl = units * (S(t_i) - K)
  cumulative += period_pnl
  if cumulative >= target:
    payoff = target  (partial fill)
    terminate
Final payoff = cumulative (if never hit target)
```

**Constructor:**
```python
TARF(
    trade_id: str,
    maturity: float,
    notional: float,
    asset_indices: tuple[int, ...],
    strike: float,
    target: float,         # cumulative profit cap
    leverage: float,       # multiplier for unfavorable side
    side: str,             # "buy" / "sell"
    schedule: list[float], # observation dates
)
```

`requires_full_path = True`. Category: Periodic.

## 5. New Modifier Design

### 5.1 TargetProfit

Generic modifier that wraps any periodic instrument and terminates when cumulative payoff hits a target. This is the composable building block — e.g. `TargetProfit(Accumulator(...))` creates TARF-like behavior from existing instruments.

**Relationship to TARF:** TARF (Section 4.6) is a self-contained instrument with FX-specific conventions (leverage, side, partial fill logic baked in). TargetProfit is the generic modifier for adding target-accrual termination to any periodic instrument. Both exist because:
- TARF encapsulates specific market conventions that FX desks expect as a single product
- TargetProfit enables target-accrual behavior on instruments where it isn't built in (e.g. a vanilla Accumulator, or future periodic instruments)

**Effect on payoff:**
```
cumulative = 0
for each observation:
    cumulative += period_payoff
    if cumulative >= target:
        if partial_fill:
            return target
        else:
            return cumulative  (overshoot allowed)
        terminate
return cumulative
```

**Constructor:**
```python
TargetProfit(
    inner,                  # wrapped instrument
    target: float,          # cumulative payoff cap
    partial_fill: bool = True,  # pro-rate last fixing
)
```

### 5.2 Barrier Modifier Enhancements

All four barrier modifiers gain observation style parameters. Backward compatible — all new parameters have defaults matching current behavior.

#### BaseModifier signature change

The current `BaseModifier._apply()` signature is `_apply(self, raw_payoff, spots, path_history)` — it does not receive `t_grid`. The observation style logic needs `t_grid` to map observation dates to path indices. This requires extending both `payoff()` and `_apply()`:

```python
# BaseModifier.payoff() — pass t_grid through to _apply:
def payoff(self, spots, path_history, t_grid=None):
    raw_payoff = self._inner.payoff(spots, path_history, t_grid)
    return self._apply(raw_payoff, spots, path_history, t_grid)

# BaseModifier._apply() — new signature:
def _apply(self, raw_payoff, spots, path_history, t_grid=None) -> np.ndarray:
    ...
```

This is a breaking change to the internal modifier interface. All 8 existing modifier `_apply()` implementations must be updated to accept `t_grid=None` (even if they ignore it). This is mechanical — add `t_grid=None` to each `_apply` signature. No behavioral changes for existing modifiers.

**New parameters for KnockOut:**
```python
KnockOut(
    inner,
    barrier: float,
    direction: str,              # "up" / "down"
    asset_idx: int = None,
    observation_style: str = "continuous",  # NEW: "continuous" / "discrete" / "window"
    observation_dates: list[float] = None,  # NEW: required if style="discrete"
    window_start: float = None,             # NEW: required if style="window"
    window_end: float = None,               # NEW: required if style="window"
    rebate: float = 0.0,                    # NEW: fixed payment on knock-out
)
```

**New parameters for KnockIn** — same as KnockOut minus `rebate`.

**New parameters for RealizedVolKnockOut / RealizedVolKnockIn** — same as KnockIn (observation style parameters only). For these vol-based modifiers, the observation style controls which portion of the path is used to compute realized vol (not just when the threshold is checked):
- **Continuous**: compute realized vol from the full path (current behavior)
- **Discrete**: compute realized vol only from prices at specified observation dates
- **Window**: compute realized vol only from the `[window_start, window_end]` sub-path

**Implementation logic:**
```python
def _get_monitored_prices(self, path_history, t_grid):
    prices = path_history[:, :, self._monitor_pos]
    if self.observation_style == "continuous":
        return prices  # all steps (current behavior)
    elif self.observation_style == "discrete":
        indices = [nearest_index(t_grid, t) for t in self.observation_dates]
        return prices[:, indices]
    elif self.observation_style == "window":
        mask = (t_grid >= self.window_start) & (t_grid <= self.window_end)
        return prices[:, mask]
```

## 6. Per-Product Documentation

A comprehensive product catalog document (`docs/product-catalog.md`) will contain entries for all 21 instruments and 9 modifiers using standardized templates.

### Instrument entry template

```
## [Product Name]

**Category:** European / Path-dependent / Multi-asset / Periodic
**Assets:** 1 / 2 / 2-5
**Path required:** Yes / No
**Module:** pfev2.instruments.[module]

### Description
1-2 sentence plain-English description.

### Payoff Formula
Mathematical formula for the payoff.

### Parameters
| Parameter | Type | Description |
|---|---|---|

### Typical Use Case
When and why a desk would trade this.

### Common Modifier Pairings
Bullet list of common modifier combinations.

### PFE Behavior
How PFE evolves over the trade's life. 2-3 sentences.

### Risk Characteristics
Key Greeks / exposure drivers. 2-3 sentences.

### Comparison
How this differs from similar products.

### Worked Example
Concrete numbers showing construction and expected payoff.
```

### Modifier entry template

```
## [Modifier Name]

**Group:** Barrier / Payoff shaper / Structural
**Module:** pfev2.modifiers.[module]

### Description
What it does to the wrapped instrument.

### Observation Styles (barrier modifiers only)
Continuous / Discrete / Window descriptions.

### Parameters
| Parameter | Type | Description |

### Effect on Payoff
Formula showing transformation.

### Effect on PFE
How this modifier changes the PFE profile.

### Typical Pairings
Which instruments this is commonly used with and why.

### Worked Example
```

## 7. File Changes

### New files

| File | Description |
|---|---|
| `docs/product-catalog.md` | Full product catalog with all instrument/modifier entries |
| `pfev2/instruments/single_barrier.py` | SingleBarrier class |
| `pfev2/instruments/asian.py` | AsianOption class |
| `pfev2/instruments/cliquet.py` | Cliquet class |
| `pfev2/instruments/range_accrual.py` | RangeAccrual class |
| `pfev2/instruments/autocallable.py` | Autocallable class |
| `pfev2/instruments/tarf.py` | TARF class |
| `pfev2/modifiers/target_profit.py` | TargetProfit class |
| `tests/test_instruments/test_single_barrier.py` | SingleBarrier tests |
| `tests/test_instruments/test_asian.py` | AsianOption tests |
| `tests/test_instruments/test_cliquet.py` | Cliquet tests |
| `tests/test_instruments/test_range_accrual.py` | RangeAccrual tests |
| `tests/test_instruments/test_autocallable.py` | Autocallable tests |
| `tests/test_instruments/test_tarf.py` | TARF tests |
| `tests/test_modifiers/test_target_profit.py` | TargetProfit tests |
| `tests/test_modifiers/test_observation_styles.py` | Barrier observation style tests |

### Modified files

| File | Changes |
|---|---|
| `pfev2/instruments/__init__.py` | Add new exports, organize by category |
| `pfev2/modifiers/__init__.py` | Add TargetProfit export |
| `pfev2/modifiers/knock_out.py` | Add observation_style, observation_dates, window_start, window_end, rebate |
| `pfev2/modifiers/knock_in.py` | Add observation_style, observation_dates, window_start, window_end |
| `pfev2/modifiers/realized_vol_knock.py` | Add observation_style, observation_dates, window_start, window_end |
| `pfev2/instruments/vanilla.py` | Add docstrings matching catalog |
| `pfev2/instruments/digital.py` | Add docstrings |
| `pfev2/instruments/barrier.py` | Add docstrings |
| `pfev2/instruments/accumulator.py` | Add docstrings |
| `pfev2/instruments/worst_best_of.py` | Add docstrings |
| `pfev2/instruments/forward_starting.py` | Add docstrings |
| `pfev2/instruments/restrike.py` | Add docstrings |
| `pfev2/instruments/contingent.py` | Add docstrings |
| `pfev2/modifiers/base.py` | Add docstrings |
| `pfev2/modifiers/cap_floor.py` | Add docstrings |
| `pfev2/modifiers/leverage.py` | Add docstrings |
| `pfev2/modifiers/schedule.py` | Add docstrings |
| `ui/utils/registry.py` | Add new instruments/modifiers, update categories and descriptions |
| `README.md` | Update instrument/modifier tables to new taxonomy |

### Out of scope

- UI pages (wizard/dashboard) — not present in GitHub version
- Pricing engine changes — `InnerMCPricer` handles `payoff()` + `requires_full_path` generically
- Risk calculator changes — works with any `BaseInstrument` implementation
- `BaseModifier._apply()` signature is extended to include `t_grid` (see Section 5.2) — this is an in-scope internal interface change, but does not cascade to pricing engine or risk calculator. All existing modifier updates are mechanical (add `t_grid=None` parameter to each `_apply` method)
