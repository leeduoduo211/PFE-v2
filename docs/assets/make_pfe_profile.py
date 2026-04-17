"""Generate the PFE/EPE profile hero image used in README.md and the wiki Home.

Run from the project root:
    python3 docs/assets/make_pfe_profile.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pfev2 import MarketData, PFEConfig, compute_pfe
from pfev2.instruments import VanillaOption, WorstOfOption

OUT = Path(__file__).parent / "pfe_profile.png"

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

config = PFEConfig(n_outer=2000, n_inner=1000, seed=42, grid_frequency="monthly")
result = compute_pfe(portfolio, market, config)

t = np.asarray(result.time_points)
pfe = np.asarray(result.pfe_curve)
epe = np.asarray(result.epe_curve)

fig, ax = plt.subplots(figsize=(10, 5), dpi=140)
ax.fill_between(t, 0, pfe, color="#dc2626", alpha=0.10, label="_nolegend_")
ax.plot(t, pfe, color="#dc2626", linewidth=2.5, label="PFE (95th percentile)")
ax.plot(t, epe, color="#2563eb", linewidth=2.0, linestyle="--", label="EPE (expected positive exposure)")

peak_idx = int(np.argmax(pfe))
ax.annotate(
    f"Peak PFE: {pfe[peak_idx]:,.0f}",
    xy=(t[peak_idx], pfe[peak_idx]),
    xytext=(t[peak_idx] + 0.12, pfe[peak_idx] * 0.92),
    fontsize=10, color="#b91c1c",
    arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.2),
)

ax.set_xlabel("Time (years)", fontsize=11)
ax.set_ylabel("Exposure (USD)", fontsize=11)
ax.set_title(
    "Potential Future Exposure — 2-asset portfolio (vanilla call + worst-of put)",
    fontsize=12, pad=12,
)
ax.grid(True, alpha=0.25, linewidth=0.5)
ax.legend(loc="upper left", fontsize=10, frameon=False)
ax.set_xlim(0, t[-1])
ax.set_ylim(bottom=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print(f"Saved: {OUT}")
print(f"Peak PFE: {pfe[peak_idx]:,.2f} at t={t[peak_idx]:.3f}y")
print(f"EEPE:     {result.eepe:,.2f}")
