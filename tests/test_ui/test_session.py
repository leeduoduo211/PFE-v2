from ui.utils import session


def test_invalidate_results_clears_latest_result_and_run_history(monkeypatch):
    state = {
        "latest_result": {"peak_pfe": 123.0},
        "runs": [{"label": "Run #1"}],
        "run_counter": 1,
    }
    monkeypatch.setattr(session.st, "session_state", state)

    session.invalidate_results()

    assert "latest_result" not in state
    assert state["runs"] == []
    assert state["run_counter"] == 0


def test_invalidate_results_can_keep_run_history(monkeypatch):
    state = {
        "latest_result": {"peak_pfe": 123.0},
        "runs": [{"label": "Base Case"}],
    }
    monkeypatch.setattr(session.st, "session_state", state)

    session.invalidate_results(clear_runs=False)

    assert "latest_result" not in state
    assert state["runs"] == [{"label": "Base Case"}]


def test_add_run_uses_custom_unique_labels(monkeypatch):
    state = {"runs": []}
    monkeypatch.setattr(session.st, "session_state", state)

    first = session.add_run({"peak_pfe": 100.0}, label="Base Case")
    second = session.add_run({"peak_pfe": 200.0}, label="Base Case")

    assert first["label"] == "Base Case"
    assert second["label"] == "Base Case (2)"
    assert state["runs"] == [first, second]


def test_select_run_sets_latest_result(monkeypatch):
    run = {"label": "Stress Up", "peak_pfe": 321.0}
    state = {"runs": [run], "latest_result": {"label": "Old"}}
    monkeypatch.setattr(session.st, "session_state", state)

    assert session.select_run("Stress Up") is True
    assert state["latest_result"] == run


def test_request_portfolio_tab_sets_switch_flag(monkeypatch):
    state = {}
    monkeypatch.setattr(session.st, "session_state", state)

    session.request_portfolio_tab()

    assert state["_switch_to_portfolio"] is True
