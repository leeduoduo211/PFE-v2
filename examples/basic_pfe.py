"""Basic PFE example: 2-asset portfolio with a vanilla call and a worst-of put."""
import numpy as np
from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import VanillaOption, WorstOfOption

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
    VanillaOption(trade_id="C1", maturity=1.0, notional=100_000,
                  asset_indices=(0,), strike=100.0, option_type="call"),
    WorstOfOption(trade_id="WP1", maturity=1.0, notional=100_000,
                  asset_indices=(0, 1), strikes=[100.0, 50.0], option_type="put"),
]

config = PFEConfig(n_outer=500, n_inner=500, seed=42, grid_frequency="monthly")

print("Running PFE calculation...")
result = compute_pfe(portfolio, market, config, on_progress=lambda p: print(f"  {p:.0%}"))
print()
print(result.summary())
