"""Per-category registry entries, merged into a single dict.

Split from the monolithic `ui/utils/registry.py` so adding a new instrument
only touches one file. The aggregator below preserves import compatibility —
`from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY` still
works because `registry.py` re-exports from here.
"""

from ui.utils.registries.european import ENTRIES as _EUROPEAN
from ui.utils.registries.modifiers import ENTRIES as _MODIFIERS
from ui.utils.registries.multi_asset import ENTRIES as _MULTI_ASSET
from ui.utils.registries.path_dependent import ENTRIES as _PATH_DEPENDENT
from ui.utils.registries.periodic import ENTRIES as _PERIODIC

# Merge in the display-order the UI cares about: European → Path-dependent →
# Multi-asset → Periodic. Within each category, entries are in the order they
# are declared in the category file.
INSTRUMENT_REGISTRY = {
    **_EUROPEAN,
    **_PATH_DEPENDENT,
    **_MULTI_ASSET,
    **_PERIODIC,
}

MODIFIER_REGISTRY = dict(_MODIFIERS)

__all__ = ["INSTRUMENT_REGISTRY", "MODIFIER_REGISTRY"]
