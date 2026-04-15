from pfev2.instruments.vanilla import VanillaCall, VanillaPut
from pfev2.instruments.digital import Digital, DualDigital, TripleDigital
from pfev2.instruments.worst_best_of import WorstOfCall, WorstOfPut, BestOfCall, BestOfPut
from pfev2.instruments.barrier import DoubleNoTouch
from pfev2.instruments.accumulator import Accumulator
from pfev2.instruments.forward_starting import ForwardStartingOption
from pfev2.instruments.restrike import RestrikeOption
from pfev2.instruments.contingent import ContingentOption
from pfev2.instruments.asian import AsianOption
from pfev2.instruments.cliquet import Cliquet
from pfev2.instruments.autocallable import Autocallable

# Decumulator is an alias — Accumulator(side="sell")
Decumulator = Accumulator

__all__ = [
    "VanillaCall", "VanillaPut",
    "Digital", "DualDigital", "TripleDigital",
    "WorstOfCall", "WorstOfPut", "BestOfCall", "BestOfPut",
    "DoubleNoTouch",
    "Accumulator", "Decumulator",
    "ForwardStartingOption", "RestrikeOption", "ContingentOption",
    "AsianOption",
    "Cliquet",
    "Autocallable",
]
