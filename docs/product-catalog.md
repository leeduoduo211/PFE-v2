# PFE-v2 Product Catalog

This catalog covers all instruments and modifiers available in the PFE-v2 library. Each entry documents the payoff mechanics, parameters, typical use cases, and PFE behavior drawn directly from the source implementation.

The library is organized into two layers: **instruments** (standalone pricing objects that compute terminal payoffs) and **modifiers** (composable wrappers that transform an inner instrument's payoff). Modifiers chain arbitrarily, so a single trade can carry multiple barrier, shaper, and structural modifiers simultaneously.

---

## Taxonomy Overview

| Product | Category | Assets | Path Required | Module |
|---|---|---|---|---|
| VanillaOption | European | 1 | No | `pfev2.instruments.vanilla` |
| Digital | European | 1 | No | `pfev2.instruments.digital` |
| ContingentOption | European | 2 | No | `pfev2.instruments.contingent` |
| SingleBarrier | European | 1 | No | `pfev2.instruments.single_barrier` |
| DoubleNoTouch | Path-dependent | 1 | Yes | `pfev2.instruments.barrier` |
| ForwardStartingOption | Path-dependent | 1 | Yes | `pfev2.instruments.forward_starting` |
| RestrikeOption | Path-dependent | 1 | Yes | `pfev2.instruments.restrike` |
| AsianOption | Path-dependent | 1 | Yes | `pfev2.instruments.asian` |
| Cliquet | Path-dependent | 1 | Yes | `pfev2.instruments.cliquet` |
| RangeAccrual | Path-dependent | 1 | Yes | `pfev2.instruments.range_accrual` |
| WorstOfOption | Multi-asset | 2–5 | No | `pfev2.instruments.worst_best_of` |
| BestOfOption | Multi-asset | 2–5 | No | `pfev2.instruments.worst_best_of` |
| Dispersion | Multi-asset | 2–5 | No | `pfev2.instruments.dispersion` |
| DualDigital | Multi-asset | 2 | No | `pfev2.instruments.digital` |
| TripleDigital | Multi-asset | 3 | No | `pfev2.instruments.digital` |
| Accumulator | Periodic | 1 | Yes | `pfev2.instruments.accumulator` |
| Autocallable | Periodic | 1–5 | Yes | `pfev2.instruments.autocallable` |
| TARF | Periodic | 1 | Yes | `pfev2.instruments.tarf` |

---

## Modifier Compatibility Matrix

| Modifier | Group | Instruments commonly paired with |
|---|---|---|
| KnockOut | Barrier | VanillaOption, AsianOption, Cliquet, RangeAccrual |
| KnockIn | Barrier | VanillaOption, Digital, ForwardStartingOption |
| RealizedVolKnockOut | Barrier | Accumulator, TARF, Cliquet, RangeAccrual |
| RealizedVolKnockIn | Barrier | VanillaOption, AsianOption, Cliquet |
| PayoffCap | Payoff shaper | VanillaOption, ForwardStartingOption, Cliquet, RangeAccrual |
| PayoffFloor | Payoff shaper | VanillaOption, Autocallable, Accumulator |
| LeverageModifier | Payoff shaper | VanillaOption, ForwardStartingOption, BestOfOption |
| ObservationSchedule | Structural | DoubleNoTouch, KnockOut, KnockIn, RangeAccrual |
| TargetProfit | Structural | Accumulator, RangeAccrual |

---

# Instruments

## European Options

---

## VanillaCall

**Category:** European
**Assets:** 1
**Path required:** No
**Module:** `pfev2.instruments.vanilla`

### Description

The plain European call option: the holder receives the excess of the spot price over the strike at maturity, or nothing if the spot finishes below the strike. It is the foundational building block from which most structured products are derived.

### Payoff Formula

```
Payoff = max(S(T) - K, 0)
```

where `S(T)` is the spot at maturity and `K` is the strike.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Time to maturity in years. Must be positive. |
| `notional` | float | Notional scaling applied by the engine. |
| `asset_indices` | list[int] | Length-1 list identifying the underlying asset. |
| `strike` | float | Strike price. Must be positive. |

### Typical Use Case

Directional long-volatility exposure on a single equity, FX rate, or commodity. Frequently used as a benchmark or as a sub-component of more complex structured products such as autocallables.

### Common Modifier Pairings

- `KnockOut` to create an up-and-out call (limits upside, cheaper premium).
- `KnockIn` to create a down-and-in call (cheap protection if market falls sharply first).
- `PayoffCap` to impose an upside cap (turning it into a call spread).
- `LeverageModifier` for enhanced participation above a threshold.

### PFE Behavior

PFE starts near zero for at-the-money options, grows as the option moves into the money through diffusion, and peaks somewhere between 30–60% of maturity depending on vol. Toward expiry, PFE collapses as time value decays and the uncertain region narrows. The profile is broadly convex in the early-to-mid trade life.

### Risk Characteristics

Delta is positive and grows toward 1 as the option moves deep in the money. Vega dominates the middle of the trade life and is the primary driver of PFE in high-vol regimes. Theta bleeds value continuously, compressing PFE as maturity approaches.

### Comparison

VanillaCall differs from Digital in that it has a continuous, unbounded payoff above the strike rather than a binary jump. It differs from ForwardStartingOption in that the strike is known at inception rather than set later. Compared to SingleBarrier, the vanilla has no path-contingent extinguishment or activation.

### Worked Example

- Spot = 100, Strike = 100, Maturity = 1 year.
- At expiry: S(T) = 110 → Payoff = 10; S(T) = 95 → Payoff = 0.
- With Notional = 1,000,000 and S(T) = 110, the cash settlement = 100,000.

---

## VanillaPut

**Category:** European
**Assets:** 1
**Path required:** No
**Module:** `pfev2.instruments.vanilla`

### Description

The plain European put option: the holder receives the excess of the strike over the spot at maturity, providing downside protection or a short-spot view.

### Payoff Formula

```
Payoff = max(K - S(T), 0)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Time to maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Length-1 list identifying the underlying. |
| `strike` | float | Strike price. Must be positive. |

### Typical Use Case

Tail-risk hedging: protect a long equity portfolio against a decline. Also used by counterparties selling capital-protected notes where the issuer is structurally long a put.

### Common Modifier Pairings

- `KnockOut` (up-and-out put): eliminates protection if the market rallies strongly.
- `KnockIn` (down-and-in put): cheaper hedge that only activates on a sharp move down.
- `PayoffFloor` to guarantee a minimum recovery value.

### PFE Behavior

PFE rises as the spot falls, peaking when the put is deep in the money. In practice, for a counterparty that sold a put, PFE is highest when the equity market has sold off, creating wrong-way risk if the counterparty is also correlated with the market.

### Risk Characteristics

Delta is negative (protective short-delta exposure). Vega is positive: the put becomes more valuable when implied vol increases. Gamma is highest at the money, making the instrument convex in spot.

### Comparison

VanillaPut is the mirror of VanillaCall. Compared to WorstOfPut, the vanilla put references a single asset rather than the worst performer in a basket. Compared to Digital put, the payoff is continuous rather than binary.

### Worked Example

- Spot = 100, Strike = 100, Maturity = 1 year.
- At expiry: S(T) = 85 → Payoff = 15; S(T) = 105 → Payoff = 0.

---

## Digital

**Category:** European
**Assets:** 1
**Path required:** No
**Module:** `pfev2.instruments.digital`

### Description

A cash-or-nothing binary option that pays exactly 1 unit (scaled by notional) if the spot finishes on the correct side of the strike at maturity, and zero otherwise. The payoff is discontinuous at the strike.

### Payoff Formula

```
Call: Payoff = 1  if S(T) > K,  else 0
Put:  Payoff = 1  if S(T) < K,  else 0
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Time to maturity in years. |
| `notional` | float | Cash amount paid on exercise. |
| `asset_indices` | list[int] | Length-1 list identifying the underlying. |
| `strike` | float | Barrier strike level. Must be positive. |
| `option_type` | str | `"call"` or `"put"`. Defaults to `"call"`. |

### Typical Use Case

Fixed-return structured notes, rebate legs in barrier trades, binary event bets (e.g., central bank decisions, earnings triggers). Also used as components inside more complex payoffs where a binary gate is needed.

### Common Modifier Pairings

- `KnockOut` to extinguish the binary if a separate barrier is breached before maturity.
- `ObservationSchedule` to restrict when the barrier event is assessed.

### PFE Behavior

PFE is highest when the spot is hovering near the strike with significant time remaining, because a small move either way determines the full notional. PFE collapses abruptly at maturity: the payoff is either full notional or zero, with no gradual decay unlike vanilla options.

### Risk Characteristics

Delta spikes sharply near the strike (approaching a Dirac delta in the Black-Scholes limit), making the instrument very sensitive to small moves near expiry. Vega is also peaked at the money but can flip sign depending on moneyness. Gamma is extreme near the strike.

### Comparison

Unlike VanillaCall, the Digital has a bounded, discontinuous payoff. DualDigital extends this to two assets with a joint condition. TripleDigital to three assets.

### Worked Example

- Strike = 100, Maturity = 1 year, option_type = "call", Notional = 50,000.
- S(T) = 102 → Payoff = 1 unit → Cash = 50,000.
- S(T) = 98 → Payoff = 0 → Cash = 0.

---

## ContingentOption

**Category:** European
**Assets:** 2
**Path required:** No
**Module:** `pfev2.instruments.contingent`

### Description

A vanilla option on a target asset whose payoff is gated by a separate trigger asset finishing on the correct side of its barrier at maturity. Both conditions are assessed at expiry only — no path monitoring.

### Payoff Formula

```
trigger_met = 1{S_trigger(T) > barrier}   (direction="up")
            = 1{S_trigger(T) < barrier}   (direction="down")

Payoff = trigger_met * max(sign * (S_target(T) - K_target), 0)
```

where `sign = +1` for a call and `sign = -1` for a put on the target.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Time to maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Length-2 list: [trigger_asset_idx, target_asset_idx]. |
| `trigger_asset_idx` | int | Global index of the trigger underlying. |
| `trigger_barrier` | float | Barrier level for the trigger asset. |
| `trigger_direction` | str | `"up"` or `"down"`: direction the trigger must breach. |
| `target_asset_idx` | int | Global index of the payout underlying. |
| `target_strike` | float | Strike on the target vanilla. |
| `target_type` | str | `"call"` or `"put"` on the target asset. |

### Typical Use Case

Correlation trades where the desk wants vanilla exposure on one asset only when a macro signal (another asset) is in the right zone. Example: pay an FX call only if the equity index closes above its trigger level.

### Common Modifier Pairings

- `KnockOut` or `KnockIn` applied to the whole structure if additional path-based conditions are needed.
- `PayoffCap` to bound the target vanilla's upside.

### PFE Behavior

PFE depends on the joint distribution of both assets. Correlation between the trigger and target assets is the key driver: positive correlation (trigger and target moving together) inflates PFE, while negative correlation deflates it. PFE is lower than a standalone VanillaCall on the target because there is a probability the trigger condition is not met.

### Risk Characteristics

Delta with respect to the target asset is conditional on the trigger being in the money, creating a non-linear, correlation-sensitive profile. The trade has implicit vega on both assets and a strong cross-gamma term that vanilla Greeks do not capture.

### Comparison

Compared to a DualDigital, the ContingentOption has an unbounded continuous payoff on the target rather than a fixed binary. Compared to a standalone VanillaCall, it is cheaper because the trigger gate reduces the probability of a non-zero payoff.

### Worked Example

- Trigger: asset 0, barrier = 3000 (index), direction = "up".
- Target: asset 1, call with strike = 1.10 (FX rate).
- At maturity: S_trigger = 3050 (above 3000) and S_target = 1.15 → Payoff = 0.05.
- At maturity: S_trigger = 2900 (below 3000) → Payoff = 0 regardless of FX rate.

---

## SingleBarrier

**Category:** European
**Assets:** 1
**Path required:** No
**Module:** `pfev2.instruments.single_barrier`

### Description

A European-style barrier option where the barrier condition is evaluated only at maturity (not continuously). This differs from the KnockOut/KnockIn path modifiers, making it a purely terminal-observation instrument.

### Payoff Formula

```
barrier_condition = (S(T) > barrier)  for direction="up"
                  = (S(T) < barrier)  for direction="down"

barrier_type="in":
  Payoff = vanilla_payoff * 1{barrier_condition_met}

barrier_type="out":
  Payoff = vanilla_payoff * 1{barrier_condition_NOT_met}
```

where `vanilla_payoff = max(S(T) - K, 0)` for a call or `max(K - S(T), 0)` for a put.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Time to maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Length-1 list identifying the underlying. |
| `strike` | float | Vanilla option strike. Must be positive. |
| `barrier` | float | Terminal barrier level. Must be positive. |
| `option_type` | str | `"call"` or `"put"`. |
| `barrier_direction` | str | `"up"` or `"down"`. |
| `barrier_type` | str | `"in"` or `"out"`. |

### Typical Use Case

Structurers use terminal-observation barriers when the client wants a simpler product that avoids the path-monitoring complexity (and higher delta-hedging cost) of continuous barriers. Common in equity-linked notes with a maturity-only capital protection trigger.

### Common Modifier Pairings

- `PayoffCap` to limit upside on in-barrier calls.
- `ObservationSchedule` is less relevant here since observation is already terminal.

### PFE Behavior

Because the barrier is only assessed at maturity, the PFE profile is smoother than for continuous-barrier products. PFE grows monotonically up to a pre-expiry peak then collapses rapidly at maturity when the terminal condition resolves.

### Risk Characteristics

For an up-and-in call, delta is zero when the spot is far below the barrier and spikes as the spot approaches the barrier from below. The terminal-only observation means there is no early-knock path premium, making it cheaper than a continuous-barrier equivalent.

### Comparison

The key distinction from `KnockOut`/`KnockIn` modifiers wrapping a vanilla is that those modifiers monitor the full path continuously. `SingleBarrier` is entirely path-independent and only checks the spot at T. It is closer in spirit to a `ContingentOption` where the trigger and target are the same asset.

### Worked Example

- Call, strike = 100, barrier = 110, direction = "up", type = "in", maturity = 1 year.
- S(T) = 115 → barrier_condition met (115 > 110) AND call in the money → Payoff = 5.
- S(T) = 108 → barrier_condition NOT met (108 < 110) → Payoff = 0 even though call is in the money.
- S(T) = 95 → Payoff = 0 (call out of the money regardless).

---

# Path-Dependent Options

---

## DoubleNoTouch

**Category:** Path-dependent
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.barrier`

### Description

A binary option that pays 1 unit if the spot price never touches either barrier during the entire life of the trade. The payoff collapses to zero the instant either the lower or upper barrier is breached.

### Payoff Formula

```
Payoff = 1  if lower <= S(t) <= upper  for all t in [0, T]
       = 0  otherwise
```

The instrument checks `min(path) >= lower` AND `max(path) <= upper`.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Time to maturity in years. |
| `notional` | float | Cash amount paid if no-touch condition holds. |
| `asset_indices` | list[int] | Length-1 list. |
| `lower` | float | Lower barrier level. Must be strictly less than `upper`. |
| `upper` | float | Upper barrier level. Must be strictly greater than `lower`. |

### Typical Use Case

Range-bound views on FX or equity: a trader who believes the currency pair will stay in a tight corridor can collect premium by selling a double no-touch. Commonly used in FX options books for event-driven positioning (pre-central bank meetings).

### Common Modifier Pairings

- `ObservationSchedule` to restrict barrier monitoring to specific dates (converting from continuous to discrete monitoring).
- `PayoffFloor` if a minimum rebate is guaranteed.

### PFE Behavior

PFE starts at the theoretical option value, then erodes rapidly as time passes — every day the barriers remain untouched, the probability of surviving to maturity increases. PFE is path-history-dependent: once both barriers have remained untouched for an extended period, the remaining PFE is low. PFE spikes if the spot approaches either barrier.

### Risk Characteristics

Vega is negative for the buyer (higher vol increases the probability of touching a barrier, reducing the value). Gamma is negative near both barriers, making the position short convexity. The trade has two delta regimes: positive delta near the lower barrier and negative delta near the upper barrier.

### Comparison

Unlike a single KnockOut, the DoubleNoTouch has two simultaneous barrier conditions. Unlike RangeAccrual, the payoff is all-or-nothing rather than proportional to time spent in range.

### Worked Example

- Lower = 95, Upper = 110, Maturity = 3 months, Notional = 100,000.
- If the path's minimum is 97.2 and maximum is 108.5 → both barriers intact → Payoff = 1 → Cash = 100,000.
- If at any point the path touches 94.9 → Payoff = 0.

---

## ForwardStartingOption

**Category:** Path-dependent
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.forward_starting`

### Description

An option whose strike is not fixed at inception but is instead set equal to the spot price at a future start date. The payoff at maturity is expressed as a performance return (percentage move from the strike-fixing date to expiry).

### Payoff Formula

```
Call: Payoff = max(S(T) / S(t_start) - 1, 0)
Put:  Payoff = max(1 - S(T) / S(t_start), 0)
```

where `t_start` is the strike-fixing date and `T` is maturity.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling (applied to the performance payoff). |
| `asset_indices` | list[int] | Length-1 list. |
| `start_time` | float | Date (years) when strike is set. Must satisfy `0 < start_time < maturity`. |
| `option_type` | str | `"call"` or `"put"`. Defaults to `"call"`. |

### Typical Use Case

Cliquets, employee stock option grants where the strike date is a future vesting date, and structured products that need volatility exposure from a future point in time rather than from today.

### Common Modifier Pairings

- `PayoffCap` to create a capped forward-start call (the building block of a Cliquet).
- `LeverageModifier` to enhance participation above a performance threshold.
- `KnockOut` to extinguish if the market moves too far before the start date.

### PFE Behavior

Before `start_time`, PFE is low because the strike has not yet been set and the trade is at-the-money by construction at that point. After `start_time`, the PFE profile resembles a standard at-the-money call's profile over the remaining `T - t_start` period. The step-up in PFE at `start_time` is a distinctive feature.

### Risk Characteristics

Vega exposure is concentrated in the forward vol from `t_start` to `T`, not in the spot vol from today. Before `t_start`, the instrument is essentially flat in spot (delta near zero). After `t_start`, delta jumps to the equivalent ATM vanilla delta. The trade is primarily a forward-vol bet.

### Comparison

RestrikeOption is similar but expressed in spot units rather than percentage performance. Cliquet decomposes a multi-period sequence of ForwardStartingOptions. A vanilla ATM call has its strike fixed at inception — here the strike is floating.

### Worked Example

- start_time = 0.5 years, maturity = 1.0 year, option_type = "call".
- S(0.5) = 105 (strike set here).
- S(1.0) = 112 → performance = 112/105 - 1 = 6.67% → Payoff = 0.0667.
- S(1.0) = 100 → performance = 100/105 - 1 = -4.76% → Payoff = 0.

---

## RestrikeOption

**Category:** Path-dependent
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.restrike`

### Description

A cliquet-style option where the strike resets to the prevailing spot on a single reset date. Unlike ForwardStartingOption, the payoff is expressed in absolute spot units rather than as a percentage performance.

### Payoff Formula

```
Call: Payoff = max(S(T) - S(t_reset), 0)
Put:  Payoff = max(S(t_reset) - S(T), 0)
```

where `t_reset` is the strike-reset date.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Length-1 list. |
| `reset_time` | float | Date (years) at which the strike resets. Must satisfy `0 < reset_time < maturity`. |
| `option_type` | str | `"call"` or `"put"`. Defaults to `"call"`. |

### Typical Use Case

Products where the client wants protection or participation from a future reference level rather than today's spot — common in equity-linked deposits and periodic reset notes. Particularly useful when the absolute level at reset is economically meaningful (e.g., mortgage-backed structures referencing a property index).

### Common Modifier Pairings

- `KnockOut` to extinguish the payoff if the market crashes before the reset date.
- `PayoffCap` to limit the maximum absolute payout.

### PFE Behavior

Similar to ForwardStartingOption: PFE is subdued before `reset_time` (the trade is at-the-money at reset by construction) and then follows an ATM option profile from `reset_time` to `T`. The key difference from ForwardStartingOption is that PFE scales with the absolute spot level at reset, not with percentage moves.

### Risk Characteristics

The delta is zero before the reset (no current spot sensitivity), then becomes standard ATM delta after reset. Vega is concentrated in the forward vol from reset to maturity. The trade has a spot-level dependency that ForwardStartingOption does not: a high reset level means a higher notional value of the remaining option.

### Comparison

ForwardStartingOption expresses performance in percentage terms (normalised), making it independent of the spot level at reset. RestrikeOption retains the absolute spot level, creating an additional source of PFE via the random strike. For a given notional, ForwardStartingOption has more stable PFE dynamics.

### Worked Example

- reset_time = 0.5 years, maturity = 1.0 year, option_type = "call".
- S(0.5) = 105 → strike set at 105.
- S(1.0) = 112 → Payoff = 7 (absolute units).
- S(1.0) = 100 → Payoff = 0.

---

## AsianOption

**Category:** Path-dependent
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.asian`

### Description

An option whose payoff is based on the arithmetic average of the spot price sampled over a discrete observation schedule, rather than the terminal spot alone. Two sub-types: fixed-strike (average price) and floating-strike (average strike).

### Payoff Formula

```
A = arithmetic_mean(S(t_i)) for t_i in schedule

average_type="price" (fixed strike):
  Call: max(A - K, 0)
  Put:  max(K - A, 0)

average_type="strike" (floating strike):
  Call: max(S(T) - A, 0)
  Put:  max(A - S(T), 0)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Length-1 list. |
| `strike` | float | Strike level (used for `average_type="price"`). |
| `option_type` | str | `"call"` or `"put"`. |
| `average_type` | str | `"price"` for fixed-strike, `"strike"` for floating-strike. |
| `schedule` | array-like[float] | Observation dates in years (e.g., monthly fixings). |

### Typical Use Case

Commodities desks use average-price options to hedge producers or consumers whose exposure is to the average price over a period rather than a single date (e.g., crude oil monthly average). Floating-strike Asians hedge cumulative average exposure vs. spot at close.

### Common Modifier Pairings

- `KnockOut` to create a knock-out Asian (cheaper, barrier extinguishes averaging).
- `ObservationSchedule` to precisely control the averaging dates.
- `PayoffCap` for capped average-price calls.

### PFE Behavior

Averaging reduces volatility of the effective underlying, so PFE is lower than a comparable vanilla option — the more observations are in the average, the greater the vol dampening. Early in the trade life, PFE grows as with a vanilla; but as observations accrue and the average hardens, PFE flattens and then collapses toward maturity.

### Risk Characteristics

Delta is lower than a vanilla (the partially-fixed average reduces spot sensitivity). Vega decreases over time as more fixings are locked in. The instrument has a characteristic "Asian vega" term that decays step-by-step with each observation.

### Comparison

VanillaCall uses only S(T); AsianOption averages across the schedule, reducing variance and hence premium. The floating-strike variant is analogous to buying the spot at the end and selling the average — it profits when S(T) > average (a bullish momentum trade).

### Worked Example

- Fixed-strike call, K = 100, schedule = [0.25, 0.5, 0.75, 1.0], maturity = 1.0.
- Observed prices: [102, 98, 105, 110] → A = 103.75.
- Payoff = max(103.75 - 100, 0) = 3.75.

---

## Cliquet

**Category:** Path-dependent
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.cliquet`

### Description

A periodic reset option that sums clipped local returns over a schedule. Each period's return is capped by `local_cap` and floored by `local_floor`; the total sum is then globally floored at `global_floor`. Effectively a series of forward-starting options with per-period and global limits.

### Payoff Formula

```
return_i = clip(S(t_i) / S(t_{i-1}) - 1, local_floor, local_cap)
total    = sum(return_i)  over all periods
Payoff   = max(total, global_floor)
```

The initial reference is S(t_0) = S(0) (trade inception spot), prepended automatically.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Length-1 list. |
| `local_cap` | float | Maximum return credited per period (e.g., 0.05 for 5%). |
| `local_floor` | float | Minimum return per period (often −∞ or a small negative, e.g., 0.0). |
| `global_floor` | float | Minimum total payoff across all periods (e.g., 0.0 for capital protection). |
| `schedule` | array-like[float] | Reset dates in years. |

### Typical Use Case

Capital-protected equity notes that offer a share of the upside each year but limit losses. Retail structured products commonly use Cliquets because the local cap/floor profile is easily explained: "You get the market return each year, capped at 5% and floored at 0%, guaranteed over 5 years."

### Common Modifier Pairings

- `PayoffCap` on the total if there is also a global cap.
- `KnockOut` to extinguish if the market falls through a hard stop-loss level.
- `RealizedVolKnockOut` to avoid paying into a high-vol regime.

### PFE Behavior

PFE is driven by the remaining un-locked periods. As each reset date passes, the local return for that period is fixed and contributes a deterministic amount to the total — this is called "locking in" and PFE declines step-by-step after each reset. In a rising market, positive locked returns accumulate, raising the floor on future payoffs; in a falling market, floored-at-zero locked returns reduce future optionality.

### Risk Characteristics

Vega is spread across multiple forward periods and is highest in the first few periods before returns start locking in. Local caps create negative gamma near the cap level each period. The global floor provides a form of convexity protection on the downside.

### Comparison

ForwardStartingOption covers one period; Cliquet covers multiple periods. RangeAccrual pays based on time-in-range rather than periodic returns. AsianOption averages the spot level, while Cliquet compounds local returns.

### Worked Example

- local_cap = 0.05, local_floor = 0.0, global_floor = 0.0.
- Schedule: [0.5, 1.0] (semi-annual, 2-period).
- S(0) = 100, S(0.5) = 106, S(1.0) = 104.
- Period 1: return = 106/100 - 1 = 6% → clipped to 5%.
- Period 2: return = 104/106 - 1 = -1.9% → clipped to 0%.
- Total = 5%, global floor = 0% → Payoff = 5%.

---

## RangeAccrual

**Category:** Path-dependent
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.range_accrual`

### Description

Pays a coupon proportional to the fraction of observation dates on which the spot price was within a specified range `[lower, upper]`. The more days spent in-range, the higher the accrued payoff.

### Payoff Formula

```
in_range_i = 1{lower <= S(t_i) <= upper}
fraction   = (count of in_range_i = 1) / (total observations)
Payoff     = fraction * coupon_rate
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling (applied to the fractional coupon). |
| `asset_indices` | list[int] | Length-1 list. |
| `lower` | float | Lower bound of the range (inclusive). Must be less than `upper`. |
| `upper` | float | Upper bound of the range (inclusive). |
| `coupon_rate` | float | Maximum coupon earned if all observations are in-range. |
| `schedule` | array-like[float] | Observation dates in years. |

### Typical Use Case

FX and rates structured notes that earn an enhanced coupon as long as the reference rate or FX rate stays in a band. Sold to clients who expect low volatility; the issuer is implicitly long volatility (short the accrual).

### Common Modifier Pairings

- `TargetProfit` to terminate early once accrued coupon reaches a target.
- `KnockOut` to eliminate future coupons if a hard barrier is hit.
- `ObservationSchedule` to precisely specify which dates count toward accrual.

### PFE Behavior

PFE accretes with each observation where the spot is in-range, building a "known accrual" floor on the final payoff. PFE rises early as uncertainty about the fraction grows, peaks in the mid-life, then declines as the majority of observations are locked in and the remaining uncertain fraction shrinks.

### Risk Characteristics

Vega is negative for the buyer (higher vol means more days out of range, reducing accrual). The trade is equivalent to a portfolio of binary digital options on each observation date. Delta is near zero when the spot is well inside the range and spikes at the boundaries.

### Comparison

DoubleNoTouch pays a fixed amount if the price never breaches either barrier; RangeAccrual pays proportionally to time spent in range and is not an all-or-nothing trade. Cliquet accrues based on returns rather than in-range indicator.

### Worked Example

- lower = 95, upper = 110, coupon_rate = 0.08 (8%), schedule = monthly over 1 year (12 dates).
- Spot stays in range for 9 of 12 months → fraction = 0.75 → Payoff = 0.75 × 0.08 = 6%.
- Notional = 1,000,000 → Cash = 60,000.

---

# Multi-Asset Options

---

## WorstOfCall

**Category:** Multi-asset
**Assets:** 2–5
**Path required:** No
**Module:** `pfev2.instruments.worst_best_of`

### Description

A call option on the worst-performing asset in a basket, expressed as relative performance versus each asset's initial reference level. The payoff is driven by whichever asset has fallen the most (or risen the least).

### Payoff Formula

```
perf_i = S_i(T) / K_i   for each asset i
worst  = min_i(perf_i)
Payoff = max(worst - 1, 0)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Asset indices in the basket. Length 2–5. |
| `strikes` | array-like[float] | Reference (initial) levels for each asset. Length must match `asset_indices`. |

### Typical Use Case

Multi-asset structured notes that enhance yield by selling basket optionality. The issuer collects extra premium because the worst-of nature reduces the probability of a meaningful payoff vs. a single-asset call. Common in equity-linked certificates referencing 3–5 large-cap stocks.

### Common Modifier Pairings

- `PayoffCap` to limit maximum upside and further reduce premium.
- `KnockOut` to extinguish if any one asset falls through a hard barrier.

### PFE Behavior

PFE is lower than a single-asset call because the worst-performer constraint means the payoff requires the weakest asset in the basket to rally. Higher pairwise correlations reduce diversification and push the PFE up; low or negative correlations drive it down. PFE peaks in the mid-life and declines to expiry.

### Risk Characteristics

Delta is concentrated on the worst-performing asset at any point; the other assets contribute minimal delta. Cross-gamma (sensitivity to pairwise spot moves) is negative — losing one asset hurts the others' contribution. The trade is short correlation: it benefits from assets moving together (all performing well) but is hurt when they diverge.

### Comparison

BestOfCall pays based on the best performer (always worth more than WorstOfCall for positive-correlation baskets). WorstOfPut is the downside mirror. A single-asset VanillaCall is a special case of WorstOfCall with one asset.

### Worked Example

- 2 assets, K = [100, 100], Maturity = 1 year.
- S1(T) = 112, S2(T) = 108 → performances = [1.12, 1.08] → worst = 1.08 → Payoff = 0.08.
- S1(T) = 115, S2(T) = 97 → worst = 0.97 → Payoff = 0 (worst asset below its strike).

---

## WorstOfPut

**Category:** Multi-asset
**Assets:** 2–5
**Path required:** No
**Module:** `pfev2.instruments.worst_best_of`

### Description

A put option on the worst-performing asset in a basket, expressed as relative performance. Pays the maximum loss of the weakest asset below its reference level.

### Payoff Formula

```
perf_i = S_i(T) / K_i
worst  = min_i(perf_i)
Payoff = max(1 - worst, 0)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Same common parameters as WorstOfCall. |
| `strikes` | array-like[float] | Reference levels for each asset. |

### Typical Use Case

The primary building block of reverse convertible notes and autocallable capital-at-risk legs. The issuer is long WorstOfPut (having sold the note), meaning they profit if any asset in the basket falls significantly — this is the "worst-of" risk that note buyers accept in exchange for an enhanced coupon.

### Common Modifier Pairings

- `PayoffFloor` to guarantee a minimum recovery (partial capital protection).
- `PayoffCap` to limit the downside exposure the issuer takes.
- `KnockIn` to activate the put only after a specific barrier breach.

### PFE Behavior

PFE rises sharply in scenarios where any asset in the basket sells off, since the put moves deep in the money. Wrong-way risk is particularly pronounced here if the counterparty's credit quality is correlated with equity market declines.

### Risk Characteristics

Delta is negative and driven by the worst-performing asset. The trade is long volatility (put value increases with vol) and long correlation (if all assets fall together, the worst-of put is more valuable than individual puts).

### Comparison

WorstOfCall requires all assets to rally; WorstOfPut only requires one to fall. BestOfPut takes the maximum individual put payoff across all assets (always worth at least as much as WorstOfPut when all puts are evaluated independently).

### Worked Example

- 2 assets, K = [100, 100], Maturity = 1 year.
- S1(T) = 95, S2(T) = 88 → worst = min(0.95, 0.88) = 0.88 → Payoff = 1 - 0.88 = 0.12.

---

## BestOfCall

**Category:** Multi-asset
**Assets:** 2–5
**Path required:** No
**Module:** `pfev2.instruments.worst_best_of`

### Description

A call option on the best-performing asset in a basket. The holder profits from the strongest mover in the group.

### Payoff Formula

```
perf_i = S_i(T) / K_i
best   = max_i(perf_i)
Payoff = max(best - 1, 0)
```

### Parameters

Same common parameters as WorstOfCall, with `strikes` array-like of float reference levels.

### Typical Use Case

Clients seeking leveraged upside exposure to the best outcome from a set of possible scenarios (e.g., "whichever of three sectors performs best"). The issuer is short correlation: if all assets move together, the best-of is not much better than a single-asset call; if they diverge, one will significantly outperform.

### Common Modifier Pairings

- `PayoffCap` to cap the maximum upside (reducing premium cost).
- `LeverageModifier` to apply extra participation above a performance level.

### PFE Behavior

PFE is higher than a single-asset VanillaCall because there are multiple assets that could drive the payoff. Higher correlation reduces the value (assets perform similarly, reducing the option to find the "best"); lower correlation increases value. PFE peaks at roughly the same timing as an ATM vanilla call.

### Risk Characteristics

Delta is driven by the current best-performing asset and shifts among assets over the trade life. The trade is short correlation and long vol spread across all assets. Cross-gamma is positive (the payoff benefits from dispersion).

### Comparison

BestOfCall is the upper bound on a basket call; WorstOfCall is the lower bound. For perfectly correlated assets, they converge.

### Worked Example

- 2 assets, K = [100, 100], Maturity = 1 year.
- S1(T) = 107, S2(T) = 115 → performances = [1.07, 1.15] → best = 1.15 → Payoff = 0.15.

---

## BestOfPut

**Category:** Multi-asset
**Assets:** 2–5
**Path required:** No
**Module:** `pfev2.instruments.worst_best_of`

### Description

Pays the maximum individual put payoff across all assets in the basket. Unlike WorstOfPut (which uses the worst performance as a single put), BestOfPut evaluates each asset's put independently and takes the highest payoff.

### Payoff Formula

```
put_i  = max(1 - S_i(T) / K_i, 0)
Payoff = max_i(put_i)
```

Note: this is NOT the put on the best performer — it is the *largest individual put payoff* across all assets.

### Parameters

Same common parameters as WorstOfCall, with `strikes` array-like of float reference levels.

### Typical Use Case

Tail-risk hedging where the portfolio manager wants protection on the worst single-asset mover, not on the "average" or "joint" decline. Useful for hedging a multi-stock book where any one stock could experience a name-specific crash.

### Common Modifier Pairings

- `PayoffFloor` for a minimum guaranteed payout.
- `KnockIn` to activate only after one asset breaches a monitoring barrier.

### PFE Behavior

BestOfPut PFE is always at least as large as any single-asset put PFE because taking the maximum only increases the payoff. In low-correlation environments it can be substantially larger. PFE grows as any one asset falls, and the profile is driven by whichever asset has moved furthest out of the money.

### Risk Characteristics

Long volatility on all assets. Long dispersion: the more the assets diverge, the more valuable it becomes to hold the best single-asset put. Delta is positive (long the worst-performing asset through the put mechanism: as any one falls, delta with respect to that asset becomes negative, increasing the hedge value).

### Comparison

WorstOfPut takes the put on the jointly worst-performing asset performance; BestOfPut takes the highest individual put payoff. For a 2-asset basket: if asset 1 falls 20% and asset 2 falls 5%, WorstOfPut pays on `1 - min(0.80, 0.95) = 0.20`, while BestOfPut also pays `max(0.20, 0.05) = 0.20` — in this case they agree. But if both are in the money, BestOfPut can exceed WorstOfPut.

### Worked Example

- 2 assets, K = [100, 100], Maturity = 1 year.
- S1(T) = 90, S2(T) = 85 → put_1 = 0.10, put_2 = 0.15 → Payoff = max(0.10, 0.15) = 0.15.

---

## DualDigital

**Category:** Multi-asset
**Assets:** 2
**Path required:** No
**Module:** `pfev2.instruments.digital`

### Description

A binary option that pays 1 unit if and only if both assets simultaneously satisfy their individual conditions at maturity. A logical AND of two single-asset digital conditions.

### Payoff Formula

```
condition_1 = S_1(T) > K_1   (call) or S_1(T) < K_1   (put)
condition_2 = S_2(T) > K_2   (call) or S_2(T) < K_2   (put)
Payoff = 1  if condition_1 AND condition_2,  else 0
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Cash amount paid if both conditions are met. |
| `asset_indices` | list[int] | Length-2 list. |
| `strikes` | list[float] | Strike levels for each asset. Length must be 2. |
| `option_types` | list[str] | `"call"` or `"put"` for each asset. Length must be 2. |

### Typical Use Case

Binary bets on joint macro events: pay out only if both the equity index is above X and the FX rate is below Y at a given date. Used in correlation products and range accrual satellites.

### Common Modifier Pairings

- `KnockOut` to add a path-monitoring barrier extinguishing the binary.
- `ObservationSchedule` to restrict the observation window.

### PFE Behavior

PFE is bounded at 1 unit (notional) and is highest when both assets are hovering near their respective strikes. Correlation between the two assets is the primary driver: positive correlation reduces the probability that both conditions are met simultaneously when they have mixed directions (one call, one put); negative correlation can increase it.

### Risk Characteristics

The trade is sensitive to the joint distribution of both assets, particularly the correlation. Each individual digital has a delta spike near its strike; the DualDigital has a delta spike only when both conditions are simultaneously near the money.

### Comparison

Single-asset Digital: one condition. DualDigital: two conditions (AND). TripleDigital: three conditions (AND). ContingentOption: one asset gates the payoff, but the other asset pays a continuous vanilla, not a binary.

### Worked Example

- Asset 1: call, K1 = 3000 (index). Asset 2: put, K2 = 1.20 (FX rate). Notional = 100,000.
- S1(T) = 3100, S2(T) = 1.18 → both conditions met → Payoff = 100,000.
- S1(T) = 3100, S2(T) = 1.22 → condition 2 fails → Payoff = 0.

---

## TripleDigital

**Category:** Multi-asset
**Assets:** 3
**Path required:** No
**Module:** `pfev2.instruments.digital`

### Description

A binary option that pays 1 unit only when all three assets simultaneously satisfy their conditions at maturity — the logical AND of three single-asset digital conditions.

### Payoff Formula

```
condition_i = S_i(T) > K_i   (call) or S_i(T) < K_i   (put)  for i = 1, 2, 3
Payoff = 1  if all three conditions met,  else 0
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Cash amount paid if all conditions met. |
| `asset_indices` | list[int] | Length-3 list. |
| `strikes` | list[float] | Strike levels for each of the three assets. Length must be 3. |
| `option_types` | list[str] | `"call"` or `"put"` for each asset. Length must be 3. |

### Typical Use Case

Bespoke correlation products for institutional clients who want yield enhancement tied to a very specific multi-asset scenario. Cheaper than DualDigital because the third condition further reduces the probability of payout.

### Common Modifier Pairings

Same as DualDigital: `KnockOut` for path-monitoring, `ObservationSchedule` for restricted windows.

### PFE Behavior

PFE is bounded at notional but is lower in absolute terms than DualDigital because the three-way AND condition has a lower probability of being satisfied. The joint sensitivity to three-asset correlation makes PFE highly model-dependent.

### Risk Characteristics

Triple joint delta spikes create significant gamma near the combined three-asset at-the-money point. Higher-order correlation (three-way) is the dominant risk factor, which is difficult to hedge with standard two-asset instruments.

### Comparison

Extends DualDigital to three assets. Each additional condition multiplicatively reduces the unconditional probability of payout, making the instrument progressively cheaper but harder to hedge and model.

### Worked Example

- Assets: index (call K=3000), FX (put K=1.20), commodity (call K=80).
- At maturity: index = 3100, FX = 1.18, commodity = 82 → all three met → Payoff = notional.
- At maturity: index = 3100, FX = 1.18, commodity = 78 → commodity fails → Payoff = 0.

---

# Periodic / Structured Products

---

## Accumulator / Decumulator

**Category:** Periodic
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.accumulator`

### Description

A series of periodic forward obligations where the holder accumulates (buys) or decumulates (sells) the underlying at a fixed strike. The obligation doubles (or multiplies by `leverage`) on each date when the spot moves against the holder's position.

### Payoff Formula

```
side="buy":
  units_i = 1            if S(t_i) >= K
           = leverage     if S(t_i) < K
  period_pnl_i = units_i * (S(t_i) - K)

side="sell":
  units_i = 1            if S(t_i) <= K
           = leverage     if S(t_i) > K
  period_pnl_i = units_i * (K - S(t_i))

Payoff = sum(period_pnl_i) over all t_i in schedule
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling per accumulated unit. |
| `asset_indices` | list[int] | Length-1 list. |
| `strike` | float | Fixed forward price for all periodic settlements. Must be positive. |
| `leverage` | float | Multiplier on units when price moves adversely. Typically 2. |
| `side` | str | `"buy"` or `"sell"`. |
| `schedule` | array-like[float] | Observation/settlement dates in years. |

### Typical Use Case

FX accumulators are popular with corporate clients who want to buy or sell foreign currency at a favorable rate (the discounted strike). The leverage feature — obligating the client to trade at 2× the volume when spot moves against them — is the hidden risk that makes the below-market strike possible.

### Common Modifier Pairings

- `TargetProfit` to terminate when cumulative profit hits a target.
- `KnockOut` to provide an upper knock-out for accumulators ("I-kill-you-later" feature in FX accumulators).
- `RealizedVolKnockOut` to terminate in high-volatility regimes.

### PFE Behavior

PFE for a buy-side accumulator is high when the spot is persistently below strike: the holder must buy at above-market rates, and with leverage × units, losses can be substantial. The path-dependent leverage structure creates asymmetric PFE: the downside (adverse path) is a large negative PFE exposure, while the upside is a series of small steady gains. The leveraged downside is the primary exposure driver for credit risk purposes.

### Risk Characteristics

Delta is always 1 unit above strike and `leverage` units below strike — the delta profile is kinked at the strike. There is no vanilla optionality: the holder is obligated (not optional) to transact. The trade is short the underlying's downside and resembles a short a series of binary put options with multiplied units.

### Comparison

TARF is an Accumulator that terminates when cumulative profit reaches a target. The Accumulator runs to full schedule regardless. Autocallable is similar in periodic structure but includes an early redemption trigger based on performance rather than profit accumulation.

### Worked Example

- side = "buy", K = 100, leverage = 2, schedule = [0.25, 0.5, 0.75, 1.0], notional per unit = 100,000.
- Observation at t=0.25: S = 105 → units = 1 → PnL = +5 → Cash = +500,000.
- Observation at t=0.5: S = 92 → units = 2 → PnL = 2 × (92 - 100) = -16 → Cash = -1,600,000.
- Observation at t=0.75: S = 95 → units = 2 → PnL = 2 × (95 - 100) = -10 → Cash = -1,000,000.

---

## Autocallable

**Category:** Periodic
**Assets:** 1–5 (worst-of on a basket)
**Path required:** Yes
**Module:** `pfev2.instruments.autocallable`

### Description

A structured note that auto-redeems early with accrued coupons if the worst-of basket performance meets or exceeds an autocall trigger on any scheduled observation date. If never called, the holder at maturity faces the full worst-of performance: principal is returned if above the put barrier, or the note suffers capital loss proportional to the worst-of shortfall.

### Payoff Formula

```
At each observation t_i (in order):
  worst_perf_i = min_j(S_j(t_i) / S_j(0))
  if (not yet called) and worst_perf_i >= autocall_trigger:
    result = coupon_rate * (i + 1)    # accrued coupon × number of periods
    trade terminates.

At maturity T (if never called):
  worst_terminal = min_j(S_j(T) / S_j(0))
  if worst_terminal >= put_strike:
    result = 0                         # principal returned (zero excess return)
  else:
    result = worst_terminal - 1.0      # capital loss: worst_perf - 100%
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years. |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Asset indices (1 for single-asset, 2–5 for worst-of). |
| `autocall_trigger` | float | Performance level triggering early call (e.g., 1.0 for 100%). Must be positive. |
| `coupon_rate` | float | Coupon per period paid on autocall (e.g., 0.06 for 6% per year). |
| `put_strike` | float | Barrier below which capital loss is incurred at maturity (e.g., 0.8 for 80%). Must be positive. |
| `schedule` | array-like[float] | Autocall observation dates in years. |

### Typical Use Case

The most widely traded structured product globally. Retail and institutional clients receive above-market coupons in exchange for: (a) risk that the note is called early (reinvestment risk), and (b) exposure to a worst-of put on the basket at maturity. Desks use Autocallables to harvest the negative correlation premium and the variance risk premium embedded in the put barrier.

### Common Modifier Pairings

- `PayoffFloor` to add minimum capital protection at maturity.
- `KnockIn` on the put leg (common variant: the put only activates if a barrier was breached during the trade life).
- `ObservationSchedule` to separate autocall observation dates from the barrier monitoring schedule.

### PFE Behavior

PFE is driven by two competing forces: (1) early-call probability, which reduces residual exposure by terminating the trade, and (2) put-at-risk on paths where the note is never called. PFE peaks before the first autocall date (maximum uncertainty about early call) and then step-declines on each observation date as some paths autocall away. The remaining worst-of put exposure creates a tail PFE that persists to maturity for deep-in-the-money put paths.

### Risk Characteristics

Short the worst-of put: the dominant risk for the issuer is a severe multi-asset drawdown that breaches the put barrier. Vega is negative on the worst-of put leg. The autocall trigger creates a path-dependent duration: average maturity is shorter in rallying markets (frequent early calls) and longer in falling markets (no calls, full put exposure).

### Comparison

An Autocallable without the put barrier would be a simple periodic digital (pays coupon if trigger met). Without the autocall feature, it reduces to a WorstOfPut. The Accumulator has periodic obligations throughout; the Autocallable has periodic triggers that can extinguish the structure entirely.

### Worked Example

- 2 assets, autocall_trigger = 1.0, coupon_rate = 0.06, put_strike = 0.8, schedule = [0.5, 1.0, 1.5, 2.0].
- At t=0.5: worst_perf = 1.02 >= 1.0 → called → result = 0.06 × 1 = 6% coupon.
- Alternative: At t=0.5: worst_perf = 0.95, at t=1.0: worst_perf = 0.82, at t=1.5: worst_perf = 0.75, at t=2.0: worst_perf = 0.72.
  - Never called, worst_terminal = 0.72 < put_strike 0.8 → result = 0.72 - 1.0 = -28% (capital loss).

---

## TARF

**Category:** Periodic
**Assets:** 1
**Path required:** Yes
**Module:** `pfev2.instruments.tarf`

### Description

A Target Accrual Redemption Forward — an accumulator that automatically terminates when the cumulative profit from all periodic settlements reaches a pre-specified target. On the fixing that would push the cumulative over the target, only the residual amount needed to reach the target is taken (partial fill).

### Payoff Formula

```
side="buy": sign = +1;  side="sell": sign = -1

For each t_i (while cumulative_pnl < target):
  units_i = 1         if S(t_i) >= K  (buy) or S(t_i) <= K  (sell)
           = leverage  otherwise
  period_pnl_i = units_i * (S(t_i) - K) * sign

  if cumulative_pnl + period_pnl_i >= target:
    result = target    # partial fill: cap at target
    terminate.
  else:
    cumulative_pnl += period_pnl_i

Payoff = target  if target hit,  else cumulative_pnl
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `trade_id` | str | Unique trade identifier. |
| `maturity` | float | Trade maturity in years (upper bound; may terminate earlier). |
| `notional` | float | Notional scaling. |
| `asset_indices` | list[int] | Length-1 list. |
| `strike` | float | Fixed forward price for periodic settlements. Must be positive. |
| `target` | float | Cumulative profit threshold that triggers early termination. Must be positive. |
| `leverage` | float | Multiplier on adverse periods. Must be positive. |
| `side` | str | `"buy"` or `"sell"`. |
| `schedule` | array-like[float] | Observation dates in years. |

### Typical Use Case

TARFs are among the most common structured FX products for corporate hedgers. A corporation buying foreign currency at a discounted strike (via an accumulator structure) is protected from unlimited accumulation by the target: once they have earned the target profit, the trade terminates and they stop being exposed to further adverse market moves.

### Common Modifier Pairings

- `KnockOut` for additional hard stop-loss on adverse paths.
- `RealizedVolKnockOut` to terminate in high-volatility environments.

### PFE Behavior

TARFs have sharply asymmetric PFE. On favorable paths (spot consistently on the profitable side of strike), the target is hit early and the trade terminates, so PFE is zero thereafter. On adverse paths, the leverage kicks in and the trade runs to full maturity with large negative cumulative PnL. The PFE profile therefore peaks early (when favorable paths terminate) and has a long tail on adverse paths. The expected life of the trade is significantly shorter than the contract maturity in favorable environments.

### Risk Characteristics

Same kinked delta as Accumulator (1 unit favorable, leverage units adverse) but with path-dependent termination. The target cap creates a positive gamma feature for the holder on favorable paths. The leverage on adverse paths creates large negative convexity. The worst-case scenario is all periods being adverse with full leverage, resulting in a loss approaching `leverage × strike_spread × number_of_periods`.

### Comparison

TARF vs. Accumulator: TARF has a built-in profit target that terminates the trade; Accumulator runs to full schedule. TARF vs. TargetProfit modifier on an Accumulator: the TARF has exact partial-fill logic (cumulative stops exactly at target); the TargetProfit modifier applies a simple cap to the already-computed cumulative, which is accurate only for monotonically increasing paths.

### Worked Example

- side = "buy", K = 100, leverage = 2, target = 10.0, schedule = [0.25, 0.5, 0.75, 1.0].
- t=0.25: S = 104 → units = 1 → PnL = +4 → cumulative = 4.
- t=0.5: S = 107 → units = 1 → PnL = +7 → cumulative would be 11 > target 10 → partial fill: result = 10. Trade terminates.
- Final payoff = 10 (not 11, not 4).

---

# Modifiers

## Barrier Modifiers

---

## KnockOut

**Group:** Barrier
**Module:** `pfev2.modifiers.knock_out`

### Description

Wraps any instrument and zeroes its payoff on paths where the monitored asset breaches the barrier at any point during the observation window. Optionally pays a fixed rebate when the knock-out event occurs.

### Observation Styles

| Style | Description |
|---|---|
| `continuous` | Full path monitored at every simulation step (default). Most conservative, highest knock-out probability. |
| `discrete` | Monitored only on specific `observation_dates`. Less frequent observation reduces knock-out probability. |
| `window` | Monitored only between `window_start` and `window_end`. Useful for European-window barriers. |

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `barrier` | float | Barrier level that triggers knock-out. |
| `direction` | str | `"up"`: knocks out when price exceeds barrier. `"down"`: knocks out when price falls below barrier. |
| `asset_idx` | int or None | Global asset index to monitor. Defaults to first asset. |
| `observation_style` | str | `"continuous"`, `"discrete"`, or `"window"`. |
| `observation_dates` | array-like or None | Required for `discrete` style. |
| `window_start` | float or None | Required for `window` style. |
| `window_end` | float or None | Required for `window` style. |
| `rebate` | float | Fixed payoff on knock-out event. Defaults to 0. |

### Effect on Payoff

```
breached = any(monitored_price > barrier)   (direction="up")
         = any(monitored_price < barrier)   (direction="down")

payoff_out = rebate   if breached
           = payoff_in  otherwise
```

### Effect on PFE

KnockOut reduces PFE by eliminating the inner payoff on breached paths. The higher the barrier (for an up-and-out) or the lower (for a down-and-out), the less frequently the knock-out fires, so the PFE reduction is small. A barrier set close to the money dramatically reduces PFE. Continuous monitoring always produces lower PFE than discrete for the same barrier level.

### Typical Pairings

- `VanillaCall` + `KnockOut(direction="up")`: up-and-out call. Classic barrier option.
- `VanillaPut` + `KnockOut(direction="down")`: down-and-out put. Cheap hedge that expires worthless if market crashes early.
- `AsianOption` + `KnockOut`: knock-out Asian, reducing premium vs. plain Asian.
- `Accumulator` + `KnockOut(direction="up")`: the classic "I-kill-you-later" FX accumulator feature.

### Worked Example

- VanillaCall, K = 100, barrier = 120, direction = "up", continuous, rebate = 0.
- Path A: max(path) = 115 → no breach → payoff = vanilla payoff (e.g., S(T) = 112 → 12).
- Path B: max(path) = 122 → barrier breached → payoff = 0 (rebate).

---

## KnockIn

**Group:** Barrier
**Module:** `pfev2.modifiers.knock_in`

### Description

Wraps any instrument and pays the inner payoff only on paths where the monitored asset has breached the barrier at some point during the observation window. If the barrier is never touched, the payoff is zero.

### Observation Styles

Same as KnockOut: `continuous`, `discrete`, `window`.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `barrier` | float | Barrier level that triggers knock-in. |
| `direction` | str | `"up"`: activates when price exceeds barrier. `"down"`: activates when price falls below barrier. |
| `asset_idx` | int or None | Global asset index to monitor. Defaults to first asset. |
| `observation_style` | str | `"continuous"`, `"discrete"`, or `"window"`. |
| `observation_dates` | array-like or None | Required for `discrete` style. |
| `window_start` | float or None | Required for `window` style. |
| `window_end` | float or None | Required for `window` style. |

### Effect on Payoff

```
activated = any(monitored_price > barrier)   (direction="up")
          = any(monitored_price < barrier)   (direction="down")

payoff_out = payoff_in   if activated
           = 0           otherwise
```

### Effect on PFE

KnockIn reduces PFE relative to a plain option because the payoff only exists on the subset of paths that have touched the barrier. PFE starts near zero (before any barrier touch is likely), rises as the probability of a knock-in increases, and then behaves like the inner instrument's PFE conditional on the barrier having been hit. KnockIn and KnockOut on the same inner instrument sum to the plain inner instrument's payoff (the parity relation).

### Typical Pairings

- `VanillaPut` + `KnockIn(direction="down")`: down-and-in put. The cheapest form of crash protection — only activates in tail scenarios.
- `ForwardStartingOption` + `KnockIn`: option only activates after a meaningful market move.
- `AsianOption` + `KnockIn`: averaging only matters if the market reaches a trigger level first.

### Worked Example

- VanillaPut, K = 100, barrier = 85, direction = "down", continuous.
- Path A: min(path) = 88 → no knock-in (never below 85) → payoff = 0 even if S(T) < 100.
- Path B: min(path) = 82 → knocked in → payoff = vanilla put payoff = max(100 - S(T), 0).

---

## RealizedVolKnockOut

**Group:** Barrier
**Module:** `pfev2.modifiers.realized_vol_knock`

### Description

Zeroes the inner payoff on any path whose realized volatility (computed from the monitored portion of the path) exceeds or falls below a volatility threshold. Unlike price barriers, the trigger is measured against the statistical dispersion of the path rather than its level.

### Observation Styles

Realized vol is computed over the portion of the path selected by `observation_style`: `continuous` (full path), `discrete` (specific dates), or `window` (time band).

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `vol_barrier` | float | Annualized vol threshold (e.g., `0.30` for 30%). Must be positive. |
| `direction` | str | `"above"`: knocked out when realized_vol > vol_barrier. `"below"`: knocked out when realized_vol < vol_barrier. |
| `asset_idx` | int or None | Global asset index to measure vol on. Defaults to first asset. |
| `annualization_factor` | float | Steps per year in the MC grid (252 daily, 52 weekly, 12 monthly). Must match simulation frequency. |
| `observation_style` | str | `"continuous"`, `"discrete"`, or `"window"`. |
| `observation_dates` | array-like or None | Required for `discrete` style. |
| `window_start` | float or None | Required for `window` style. |
| `window_end` | float or None | Required for `window` style. |

### Effect on Payoff

```
rv = annualized_std(log_returns(monitored_path)) * sqrt(annualization_factor)

knocked_out = rv > vol_barrier   (direction="above")
            = rv < vol_barrier   (direction="below")

payoff_out = 0           if knocked_out
           = payoff_in   otherwise
```

### Effect on PFE

For `direction="above"`: high-vol paths (which often have the largest payoffs for long-option positions) are eliminated, reducing PFE significantly in volatile scenarios. This creates a concave relationship between vol and PFE: PFE peaks at moderate vol levels and is cut off above the barrier. For `direction="below"`: low-vol stable paths are eliminated, concentrating PFE on the more dispersed paths.

### Typical Pairings

- `Accumulator` + `RealizedVolKnockOut(direction="above")`: terminate the accumulator if FX vol spikes, preventing extreme adverse accumulation.
- `TARF` + `RealizedVolKnockOut`: high-vol regime termination for corporate hedgers.
- `Cliquet` + `RealizedVolKnockOut(direction="below")`: only activate cliquet in high-vol environments (for vol buyers).
- `RangeAccrual` + `RealizedVolKnockOut(direction="above")`: stop accrual if market becomes too volatile.

### Worked Example

- VanillaCall wrapped in `RealizedVolKnockOut(vol_barrier=0.30, direction="above", annualization_factor=252)`.
- Path A: annualized realized vol = 0.25 → no knock-out → full vanilla payoff.
- Path B: annualized realized vol = 0.38 → knocked out → payoff = 0.

---

## RealizedVolKnockIn

**Group:** Barrier
**Module:** `pfev2.modifiers.realized_vol_knock`

### Description

Activates the inner payoff only on paths whose realized volatility exceeds or falls below a threshold. The payoff is zero on any path that does not meet the vol condition — the mirror of `RealizedVolKnockOut`.

### Observation Styles

Same as `RealizedVolKnockOut`: `continuous`, `discrete`, `window`.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `vol_barrier` | float | Annualized vol threshold. Must be positive. |
| `direction` | str | `"above"`: activated when realized_vol > vol_barrier. `"below"`: activated when realized_vol < vol_barrier. |
| `asset_idx` | int or None | Defaults to first asset. |
| `annualization_factor` | float | Steps per year. Default is 52 (weekly). |
| `observation_style` | str | `"continuous"`, `"discrete"`, or `"window"`. |
| `observation_dates` | array-like or None | Required for `discrete` style. |
| `window_start` | float or None | Required for `window` style. |
| `window_end` | float or None | Required for `window` style. |

### Effect on Payoff

```
rv = annualized_std(log_returns(monitored_path)) * sqrt(annualization_factor)

activated = rv > vol_barrier   (direction="above")
          = rv < vol_barrier   (direction="below")

payoff_out = payoff_in   if activated
           = 0           otherwise
```

### Effect on PFE

PFE is concentrated on the subset of paths whose vol profile matches the activation condition. For `direction="above"`, PFE is dominated by the high-vol tail paths (typically larger payoffs for options). The parity relation holds: RealizedVolKnockOut + RealizedVolKnockIn = inner instrument, just as for price-barrier variants.

### Typical Pairings

- `VanillaCall` + `RealizedVolKnockIn(direction="above")`: structured vol play — profit only materializes in high-vol environments.
- `AsianOption` + `RealizedVolKnockIn`: averaging only matters in volatile markets.
- `Cliquet` + `RealizedVolKnockIn(direction="above")`: cliquet activates only in volatile regimes.

### Worked Example

- VanillaCall, barrier = 0.25, direction = "above", annualization_factor = 52.
- Path A: realized vol = 0.22 → not activated → payoff = 0.
- Path B: realized vol = 0.31 → activated → payoff = vanilla call payoff.

---

## Payoff Shaper Modifiers

---

## PayoffCap

**Group:** Payoff shaper
**Module:** `pfev2.modifiers.cap_floor`

### Description

Clips the inner instrument's payoff at a fixed maximum. Any path whose raw payoff exceeds the cap is reduced to the cap level; paths below the cap are unaffected.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `cap` | float | Maximum payoff value (inclusive). Any raw payoff above this is truncated. |

### Effect on Payoff

```
payoff_out = min(payoff_in, cap)
```

### Effect on PFE

Reduces PFE on all paths where the raw payoff would have exceeded the cap. The reduction is most significant in high-vol scenarios where large payoffs become probable. PFE is bounded at `cap × notional`, creating a hard ceiling on the exposure profile. The shape of PFE changes from convex-and-growing to flat-beyond-the-cap.

### Typical Pairings

- `VanillaCall` + `PayoffCap`: creates a bull call spread equivalent (the cap corresponds to the short strike in the spread).
- `ForwardStartingOption` + `PayoffCap`: capped performance note with a bounded upside.
- `Cliquet` + `PayoffCap`: in addition to the internal `local_cap`, an outer global cap bounds total accrual.
- `RangeAccrual` + `PayoffCap`: limits total coupon payout.

### Worked Example

- VanillaCall, K = 100, with PayoffCap(cap = 0.20).
- S(T) = 125 → vanilla payoff = 0.25 → capped to 0.20.
- S(T) = 112 → vanilla payoff = 0.12 → passes through (below cap).
- S(T) = 95 → vanilla payoff = 0 → passes through (zero).

---

## PayoffFloor

**Group:** Payoff shaper
**Module:** `pfev2.modifiers.cap_floor`

### Description

Applies a minimum to the inner instrument's payoff. Any path whose raw payoff falls below the floor is raised to the floor level; paths above the floor are unaffected.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `floor` | float | Minimum payoff value (inclusive). Often 0.0 for capital protection or a positive value for guaranteed minimum return. |

### Effect on Payoff

```
payoff_out = max(payoff_in, floor)
```

### Effect on PFE

Raises the minimum PFE to at least `floor × notional`, creating a hard floor on the exposure profile. For instruments with potential negative payoffs (e.g., accumulators, TARFs on adverse paths), a floor at zero creates de facto capital protection and bounds the counterparty's maximum loss. This can dramatically change the shape of PFE: rather than declining on negative-payoff paths, PFE is held up at the floor level.

### Typical Pairings

- `Accumulator` + `PayoffFloor(floor=0.0)`: cap the accumulator's downside (makes it a one-sided accumulator).
- `Autocallable` + `PayoffFloor(floor=0.0)`: principal protection feature, guaranteeing no capital loss at maturity.
- `VanillaPut` + `PayoffFloor(floor=0.0)`: vanilla put already has an implicit floor at zero, so this is redundant; but useful to make explicit in a modifier chain.

### Worked Example

- Accumulator with buy side, periodic pnl = -15 over the schedule.
- Without floor: payoff = -15.
- With PayoffFloor(floor=0.0): payoff = max(-15, 0) = 0.

---

## LeverageModifier

**Group:** Payoff shaper
**Module:** `pfev2.modifiers.leverage`

### Description

Applies a leverage multiplier to all payoffs that exceed a specified threshold. Payoffs at or below the threshold pass through unchanged; payoffs above are scaled up by the leverage factor.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `threshold` | float | Payoff level above which leverage is applied. |
| `leverage` | float | Multiplier applied to payoffs above the threshold. |

### Effect on Payoff

```
payoff_out = payoff_in * leverage   if payoff_in > threshold
           = payoff_in              otherwise
```

### Effect on PFE

Amplifies PFE on all paths where the inner payoff exceeds the threshold. The effect is non-linear: low-payoff paths are unaffected, but high-payoff paths are multiplied by `leverage`, creating a convex kink in the PFE profile at the threshold level. In high-vol scenarios, a larger fraction of paths breach the threshold, magnifying the leverage impact.

### Typical Pairings

- `VanillaCall` + `LeverageModifier`: participation rate above a threshold — for example, 150% participation above a 5% performance threshold.
- `ForwardStartingOption` + `LeverageModifier`: enhanced return structured note with boosted upside participation.
- `BestOfCall` + `LeverageModifier`: levered best-of structure for aggressive upside betting.

### Worked Example

- VanillaCall, K = 100, with LeverageModifier(threshold = 0.05, leverage = 1.5).
- S(T) = 108 → vanilla payoff = 0.08 → above threshold 0.05 → leveraged: 0.08 × 1.5 = 0.12.
- S(T) = 103 → vanilla payoff = 0.03 → below threshold 0.05 → passes through: 0.03.
- S(T) = 95 → vanilla payoff = 0 → passes through: 0.

---

## Structural Modifiers

---

## ObservationSchedule

**Group:** Structural
**Module:** `pfev2.modifiers.schedule`

### Description

Overrides the observation dates exported by the inner instrument, restricting path sampling to a user-specified discrete schedule. The payoff itself is passed through unchanged — this modifier purely controls when the simulation engine evaluates the inner instrument, not what it pays.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument or modifier. |
| `dates` | array-like[float] | Observation dates in years from trade inception. |

### Effect on Payoff

```
payoff_out = payoff_in   (pass-through, no transformation)
```

The modifier overrides `observation_dates()` to return `dates`, causing the simulation engine to only generate path points at those times. Inner instruments that otherwise use their own internal schedule are silently overridden.

### Effect on PFE

ObservationSchedule does not directly change the payoff, but it changes the simulation granularity and the set of path time-points available to inner instruments. A barrier instrument with `observation_style="discrete"` will use the schedule to determine which time steps to check the barrier against — so an `ObservationSchedule` wrapping a `KnockOut` effectively converts it to discrete monitoring.

### Typical Pairings

- `KnockOut` + `ObservationSchedule`: convert continuous barrier to discrete monitoring (fewer observation dates = lower knock-out probability).
- `DoubleNoTouch` + `ObservationSchedule`: discretize the double no-touch barrier checks.
- `RangeAccrual` + `ObservationSchedule`: align accrual observation dates with a specific fixing schedule (e.g., monthly rather than daily).

### Worked Example

- KnockOut wrapping VanillaCall, with continuous barrier monitoring.
- Wrap in ObservationSchedule(dates=[0.25, 0.5, 0.75, 1.0]).
- The barrier is now only checked at the four quarterly dates, not every simulation step.
- Result: fewer knock-out events vs. continuous monitoring → higher effective payoff probability.

---

## TargetProfit

**Group:** Structural
**Module:** `pfev2.modifiers.target_profit`

### Description

Terminates any periodic instrument when cumulative payoff reaches a target. With `partial_fill=True` (default), the payoff is capped at exactly the target on paths that would otherwise exceed it. With `partial_fill=False`, the raw payoff is returned even if it exceeds the target.

**Design note:** This modifier sees only the final aggregate payoff, not the per-period breakdown. It implements an accurate partial fill for monotonically increasing P&L (such as buy-side accumulators in favorable markets). For instruments with oscillating P&L, the standalone `TARF` instrument (which has the target logic embedded in its per-period loop) should be preferred.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `inner` | instrument | Wrapped instrument. Must be a periodic instrument. |
| `target` | float | Cumulative profit threshold that caps the payoff. Must be positive. |
| `partial_fill` | bool | If `True` (default), cap at target. If `False`, pass through raw payoff. |

### Effect on Payoff

```
payoff_out = min(payoff_in, target)   if partial_fill=True
           = payoff_in                if partial_fill=False
```

### Effect on PFE

TargetProfit clips the right tail of the payoff distribution at `target`, reducing PFE on high-payoff paths. The PFE reduction mirrors PayoffCap in structure, but semantically TargetProfit is a trade-lifecycle termination condition rather than a market-contingent cap. The expected trade life is shortened on favorable paths, which reduces the average duration and the total credit exposure.

### Typical Pairings

- `Accumulator` + `TargetProfit`: the most natural pairing. Accumulator with a target profit converts it into a simplified TARF (with the caveat on oscillating P&L).
- `RangeAccrual` + `TargetProfit`: stop accruing once the coupon target is reached.

### Worked Example

- Accumulator (buy side) with cumulative payoff = 12.5, TargetProfit(target=10.0, partial_fill=True).
- payoff_out = min(12.5, 10.0) = 10.0.
- With partial_fill=False: payoff_out = 12.5.
