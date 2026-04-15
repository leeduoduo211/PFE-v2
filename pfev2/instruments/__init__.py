# Category 1 — European (terminal spot only)
from pfev2.instruments.vanilla import VanillaOption
from pfev2.instruments.digital import Digital
from pfev2.instruments.contingent import ContingentOption
from pfev2.instruments.single_barrier import SingleBarrier

# Category 2 — Path-dependent (single asset, full path)
from pfev2.instruments.barrier import DoubleNoTouch
from pfev2.instruments.forward_starting import ForwardStartingOption
from pfev2.instruments.restrike import RestrikeOption
from pfev2.instruments.asian import AsianOption
from pfev2.instruments.cliquet import Cliquet
from pfev2.instruments.range_accrual import RangeAccrual

# Category 3 — Multi-asset (multiple underlyings)
from pfev2.instruments.worst_best_of import WorstOfCall, WorstOfPut, BestOfCall, BestOfPut
from pfev2.instruments.digital import DualDigital, TripleDigital

# Category 4 — Periodic observation (scheduled path)
from pfev2.instruments.accumulator import Accumulator
from pfev2.instruments.autocallable import Autocallable
from pfev2.instruments.tarf import TARF

# Decumulator is an alias — Accumulator(side="sell")
Decumulator = Accumulator

__all__ = [
    # European
    "VanillaOption", "Digital", "ContingentOption", "SingleBarrier",
    # Path-dependent
    "DoubleNoTouch", "ForwardStartingOption", "RestrikeOption",
    "AsianOption", "Cliquet", "RangeAccrual",
    # Multi-asset
    "WorstOfCall", "WorstOfPut", "BestOfCall", "BestOfPut",
    "DualDigital", "TripleDigital",
    # Periodic
    "Accumulator", "Decumulator", "Autocallable", "TARF",
]
