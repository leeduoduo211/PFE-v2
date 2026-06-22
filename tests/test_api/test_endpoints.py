"""End-to-end tests for the REST API service.

All routes are under the ``/api`` prefix (so the service can share an origin
with the built SPA in the Docker image).
"""

import time

import pytest

pytest.importorskip("fastapi", reason="api extra not installed")

from fastapi.testclient import TestClient  # noqa: E402

from api.app import create_app  # noqa: E402
from api.jobs import RunStore  # noqa: E402

MARKET = {
    "spots": [100.0],
    "vols": [0.20],
    "rates": [0.05],
    "domestic_rate": 0.05,
    "corr_matrix": [[1.0]],
    "asset_names": ["AAPL"],
    "asset_classes": ["EQUITY"],
}

VANILLA_CALL = {
    "trade_id": "C1",
    "instrument_type": "VanillaOption",
    "direction": "long",
    "params": {
        "maturity": 1.0,
        "notional": 100_000,
        "asset_indices": [0],
        "strike": 100.0,
        "option_type": "call",
    },
    "modifiers": [],
}

FAST_CONFIG = {"n_outer": 40, "n_inner": 40, "seed": 7, "grid_frequency": "monthly"}


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def _wait_for_completion(client, run_id, timeout=60.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"/api/runs/{run_id}").json()
        if status["status"] in ("completed", "failed"):
            return status
        time.sleep(0.05)
    pytest.fail(f"run {run_id} did not finish within {timeout}s")


def _submit(client, **overrides):
    body = {"market": MARKET, "portfolio": [VANILLA_CALL], "config": FAST_CONFIG}
    body.update(overrides)
    return client.post("/api/runs", json=body)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_registry_schema(client):
    payload = client.get("/api/registry").json()
    assert len(payload["instruments"]) == 18
    assert len(payload["modifiers"]) == 9
    vanilla = payload["instruments"]["VanillaOption"]
    assert "cls" not in vanilla
    assert vanilla["category"] == "European"
    field_names = {f["name"] for f in vanilla["fields"]}
    assert {"strike", "option_type"} <= field_names


def test_t0_mtm_preview(client):
    resp = client.post(
        "/api/t0-mtm",
        json={"market": MARKET, "portfolio": [VANILLA_CALL], "config": FAST_CONFIG},
    )
    assert resp.status_code == 200
    values = resp.json()["per_trade_t0_mtm"]
    assert len(values) == 1
    assert values[0] > 0  # ATM call has positive value


def test_t0_mtm_validation_error(client):
    bad_market = dict(MARKET, corr_matrix=[[1.0, 0.5], [0.5, 1.0]])
    resp = client.post(
        "/api/t0-mtm",
        json={"market": bad_market, "portfolio": [VANILLA_CALL]},
    )
    assert resp.status_code == 422
    assert "corr_matrix" in resp.json()["detail"]


def test_run_lifecycle(client):
    resp = _submit(client, label="smoke run")
    assert resp.status_code == 202
    submitted = resp.json()
    run_id = submitted["run_id"]
    assert submitted["status"] in ("queued", "running")
    assert submitted["label"] == "smoke run"

    status = _wait_for_completion(client, run_id)
    assert status["status"] == "completed"
    assert status["progress"] == 1.0
    assert status["peak_pfe"] > 0

    result = client.get(f"/api/runs/{run_id}/result").json()
    n_points = len(result["time_points"])
    assert n_points == 13  # monthly grid, 1y maturity, including t=0
    assert len(result["pfe_curve"]) == n_points
    assert len(result["epe_curve"]) == n_points
    assert result["period_label"] == "months"
    assert result["peak_pfe"] == status["peak_pfe"]
    assert len(result["per_trade_t0_mtm"]) == 1
    assert result["config"]["n_outer"] == 40
    assert "mtm_matrix" not in result

    with_mtm = client.get(f"/api/runs/{run_id}/result", params={"include_mtm": True})
    matrix = with_mtm.json()["mtm_matrix"]
    assert len(matrix) == 40 and len(matrix[0]) == n_points

    runs = client.get("/api/runs").json()
    assert any(r["run_id"] == run_id for r in runs)


def test_run_rejects_empty_portfolio(client):
    resp = client.post("/api/runs", json={"market": MARKET, "portfolio": []})
    assert resp.status_code == 422  # pydantic min_length


def test_run_rejects_unknown_instrument(client):
    bad_trade = dict(VANILLA_CALL, instrument_type="FluxCapacitor")
    resp = client.post("/api/runs", json={"market": MARKET, "portfolio": [bad_trade]})
    assert resp.status_code == 422
    assert "FluxCapacitor" in resp.json()["detail"]


def test_run_rejects_bad_config(client):
    resp = client.post(
        "/api/runs",
        json={"market": MARKET, "portfolio": [VANILLA_CALL], "config": {"n_outer": -1}},
    )
    assert resp.status_code == 422
    assert "n_outer" in resp.json()["detail"]


def test_unknown_run_id(client):
    assert client.get("/api/runs/nope").status_code == 404
    assert client.get("/api/runs/nope/result").status_code == 404


def test_sse_stream_reaches_completed(client):
    run_id = _submit(client).json()["run_id"]
    # TestClient returns the full streamed body once the generator closes,
    # which it does on the terminal event.
    with client.stream("GET", f"/api/runs/{run_id}/events") as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())
    events = [
        line[len("data: ") :]
        for line in body.splitlines()
        if line.startswith("data: ")
    ]
    assert events, "stream produced no events"
    import json

    final = json.loads(events[-1])
    assert final["status"] == "completed"
    assert final["progress"] == 1.0


def test_sse_unknown_run_emits_error(client):
    with client.stream("GET", "/api/runs/nope/events") as resp:
        body = "".join(resp.iter_text())
    assert "Unknown run id" in body


def test_persistence_survives_new_store(tmp_path):
    """A completed run reloads from SQLite into a fresh store (restart sim)."""
    db_path = str(tmp_path / "runs.db")

    with TestClient(create_app(RunStore(db_path=db_path))) as c1:
        run_id = _submit(c1, label="persisted").json()["run_id"]
        _wait_for_completion(c1, run_id)
        live_result = c1.get(f"/api/runs/{run_id}/result").json()

    # New store, same DB file — simulates a process restart.
    with TestClient(create_app(RunStore(db_path=db_path))) as c2:
        runs = c2.get("/api/runs").json()
        assert any(r["run_id"] == run_id and r["label"] == "persisted" for r in runs)

        status = c2.get(f"/api/runs/{run_id}").json()
        assert status["status"] == "completed"
        assert status["peak_pfe"] == pytest.approx(live_result["peak_pfe"])

        restored = c2.get(f"/api/runs/{run_id}/result").json()
        assert restored["pfe_curve"] == live_result["pfe_curve"]
        # MtM matrix is never persisted — not available after restart.
        assert "mtm_matrix" not in restored
