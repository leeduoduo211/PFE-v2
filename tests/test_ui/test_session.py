from ui.utils import session


def test_invalidate_results_clears_latest_result_and_run_history(monkeypatch):
    state = {
        "latest_result": {"peak_pfe": 123.0},
        "runs": [{"label": "Run #1"}],
    }
    monkeypatch.setattr(session.st, "session_state", state)

    session.invalidate_results()

    assert "latest_result" not in state
    assert state["runs"] == []


def test_request_portfolio_tab_sets_switch_flag(monkeypatch):
    state = {}
    monkeypatch.setattr(session.st, "session_state", state)

    session.request_portfolio_tab()

    assert state["_switch_to_portfolio"] is True
