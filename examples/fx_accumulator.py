"""FX Accumulator with KnockOut barrier — PFE example.

Demonstrates:
- FX asset class (rate = foreign risk-free rate, domestic_rate for discounting)
- Accumulator with monthly observations
- KnockOut modifier wrapping the accumulator
- Margined PFE with 10-day MPoR
"""
import numpy as np
from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import Accumulator
from pfev2.modifiers import KnockOut

# EURUSD market data
market = MarketData(
    spots=np.array([1.085]),
    vols=np.array([0.08]),
    rates=np.array([0.02]),       # EUR risk-free rate
    domestic_rate=0.04,            # USD risk-free rate
    corr_matrix=np.array([[1.0]]),
    asset_names=["EURUSD"],
    asset_classes=["FX"],
)

# Monthly accumulator over 1 year, knocked out at 1.15
schedule = [round(i / 12, 4) for i in range(1, 13)]
acc = Accumulator(
    trade_id="ACC-EURUSD",
    maturity=1.0,
    notional=1_000_000,
    asset_indices=(0,),
    strike=1.10,
    leverage=2.0,
    side="buy",
    schedule=schedule,
)
ko_acc = KnockOut(acc, barrier=1.15, direction="up")

portfolio = [ko_acc]

# Margined config (10-day MPoR)
config = PFEConfig(
    n_outer=500, n_inner=500, seed=42,
    grid_frequency="weekly",
    margined=True, mpor_days=10,
)

print("Running margined PFE for FX Accumulator + KnockOut...")
result = compute_pfe(portfolio, market, config, on_progress=lambda p: print(f"  {p:.0%}"))
print()
print(result.summary())
