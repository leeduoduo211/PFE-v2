"""Multi-asset Worst-Of put with PayoffCap — PFE example.

Demonstrates:
- 3-asset correlated equity portfolio
- Worst-of put on all 3 underlyings
- PayoffCap modifier to limit maximum payoff
- Per-trade detail for exposure breakdown
"""
import numpy as np
from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import VanillaCall, WorstOfPut, BestOfCall
from pfev2.modifiers import PayoffCap

# 3-asset equity market
market = MarketData(
    spots=np.array([100.0, 80.0, 120.0]),
    vols=np.array([0.25, 0.30, 0.20]),
    rates=np.array([0.05, 0.05, 0.05]),
    domestic_rate=0.05,
    corr_matrix=np.array([
        [1.0, 0.6, 0.3],
        [0.6, 1.0, 0.4],
        [0.3, 0.4, 1.0],
    ]),
    asset_names=["AAPL", "TSLA", "MSFT"],
    asset_classes=["EQUITY", "EQUITY", "EQUITY"],
)

# Portfolio: worst-of put (capped) + best-of call + vanilla hedge
capped_wop = PayoffCap(
    WorstOfPut(
        trade_id="WOP-3",
        maturity=1.0,
        notional=500_000,
        asset_indices=(0, 1, 2),
        strikes=[100.0, 80.0, 120.0],
    ),
    cap=0.3,  # cap payoff at 30%
)

best_call = BestOfCall(
    trade_id="BOC-3",
    maturity=1.0,
    notional=200_000,
    asset_indices=(0, 1, 2),
    strikes=[100.0, 80.0, 120.0],
)

hedge = VanillaCall(
    trade_id="HEDGE",
    maturity=0.5,
    notional=-100_000,   # short position
    asset_indices=(0,),
    strike=105.0,
)

portfolio = [capped_wop, best_call, hedge]

config = PFEConfig(n_outer=500, n_inner=500, seed=42, grid_frequency="monthly")

print("Running PFE for 3-asset multi-trade portfolio...")
result = compute_pfe(
    portfolio, market, config,
    on_progress=lambda p: print(f"  {p:.0%}"),
    per_trade_detail=True,
)
print()
print(result.summary())
print(f"\nPer-trade MtM shape: {result.per_trade_mtm.shape}")
print(f"  (trades={result.per_trade_mtm.shape[0]}, "
      f"paths={result.per_trade_mtm.shape[1]}, "
      f"steps={result.per_trade_mtm.shape[2]})")
