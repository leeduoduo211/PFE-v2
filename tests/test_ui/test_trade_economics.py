from ui.components.trade_economics import _MODIFIER_ECONOMICS, _TERM_SHEETS, compute_scenarios
from ui.utils.product_content import PRODUCT_SCENARIOS
from ui.utils.registry import INSTRUMENT_REGISTRY, MODIFIER_REGISTRY


def _make_default_params(inst_type):
    """Build a minimal params dict from registry defaults."""
    spec = INSTRUMENT_REGISTRY[inst_type]
    params = {"maturity": 1.0, "notional": 1_000_000, "assets": ["AAPL"]}
    for field in spec["fields"]:
        if field.get("default") is not None:
            params[field["name"]] = field["default"]
        elif field["type"] == "schedule":
            params[field["name"]] = [0.25, 0.5, 0.75, 1.0]
        elif field["type"] == "float":
            params[field["name"]] = 100.0
        elif field["type"] == "select":
            params[field["name"]] = field.get("choices", ["call"])[0]
        elif field["type"] == "float_list":
            params[field["name"]] = [100.0, 100.0]
        elif field["type"] == "select_list":
            params[field["name"]] = [field.get("choices", ["call"])[0]] * 2
        elif field["type"] in ("asset_select", "asset_select_optional"):
            params[field["name"]] = 0
    n_assets = spec.get("n_assets", 1)
    if isinstance(n_assets, str):
        n_assets = int(n_assets.split("-")[0])
    if n_assets > 1:
        params["assets"] = [f"ASSET_{i}" for i in range(n_assets)]
    return params


class TestTermSheetCoverage:
    def test_every_instrument_has_builder(self):
        for key in INSTRUMENT_REGISTRY:
            assert key in _TERM_SHEETS, f"Missing _TERM_SHEETS entry for {key}"

    def test_every_builder_returns_nonempty_html(self):
        for key in INSTRUMENT_REGISTRY:
            params = _make_default_params(key)
            fn = _TERM_SHEETS[key]
            result = fn(params, "long")
            assert len(result) > 20, f"Term sheet for {key} too short"

    def test_every_builder_handles_short_direction(self):
        for key in INSTRUMENT_REGISTRY:
            params = _make_default_params(key)
            fn = _TERM_SHEETS[key]
            result = fn(params, "short")
            assert len(result) > 20


class TestModifierEconomicsCoverage:
    def test_every_modifier_has_economics(self):
        for key in MODIFIER_REGISTRY:
            assert key in _MODIFIER_ECONOMICS, f"Missing _MODIFIER_ECONOMICS for {key}"

    def test_every_economics_returns_nonempty(self):
        for key in MODIFIER_REGISTRY:
            spec = MODIFIER_REGISTRY[key]
            params = {}
            for field in spec["fields"]:
                if field.get("default") is not None:
                    params[field["name"]] = field["default"]
                elif field["type"] == "float":
                    params[field["name"]] = 1.0
                elif field["type"] == "select":
                    params[field["name"]] = field.get("choices", ["up"])[0]
                elif field["type"] == "schedule":
                    params[field["name"]] = [0.25, 0.5, 0.75, 1.0]
            fn = _MODIFIER_ECONOMICS[key]
            result = fn(params)
            assert len(result) > 10, f"Economics for {key} too short"


class TestScenarios:
    def test_compute_scenarios_returns_three_rows(self):
        spec = {
            "instrument_type": "VanillaOption",
            "params": {"strike": 100.0, "option_type": "call", "maturity": 1.0, "notional": 1e6, "assets": ["X"]},
            "modifiers": [],
            "direction": "long",
        }
        rows = compute_scenarios(spec, 100.0, 1e6)
        assert len(rows) == 3

    def test_product_scenarios_structure(self):
        for _key, scenarios in PRODUCT_SCENARIOS.items():
            for s in scenarios:
                assert "label" in s
                assert "description" in s
