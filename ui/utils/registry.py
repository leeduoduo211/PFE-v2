"""
Instrument and modifier registries for dynamic UI form generation.

The data definitions live in per-category files under `ui/utils/registries/`
(European, Path-dependent, Multi-asset, Periodic, Modifiers). This module
just aggregates them into the two public dicts callers expect.

Each registry entry maps a type name to a spec dict:
  {
      "cls":      <class>,
      "label":    <human-readable name>,
      "category": <str>,  # European / Path-dependent / Multi-asset / Periodic
      "n_assets": <int> | "2-5",  # number of required assets
      "fields":   [<field_spec>, ...],
  }

Each field_spec:
  {
      "name":     <str>,   # constructor keyword argument name
      "label":    <str>,   # UI display label
      "type":     <str>,   # one of: float, select, float_list, select_list,
                           #         asset_select, asset_select_optional, schedule
      "default":  <any>,   # optional default value
      "choices":  [<str>], # required for select / select_list
      "help":     <str>,   # optional tooltip text
  }

Adding a new instrument: drop an entry into the right category file under
`ui/utils/registries/` and it appears in the UI automatically.
"""

from ui.utils.registries import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY

__all__ = ["INSTRUMENT_REGISTRY", "MODIFIER_REGISTRY"]
