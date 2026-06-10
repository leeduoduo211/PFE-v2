"""FastAPI service exposing the pfev2 engine.

Endpoints
---------
GET  /health              – liveness probe
GET  /registry            – instrument + modifier field schemas (drives forms)
POST /t0-mtm              – synchronous per-trade t=0 MtM preview
POST /runs                – validate inputs, queue a PFE run, return 202 + id
GET  /runs                – run history, newest first
GET  /runs/{id}           – status + progress for one run
GET  /runs/{id}/result    – serialized PFEResult (404/409 until completed)

Launch:  python3 -m uvicorn api.app:app --reload
Docs:    http://127.0.0.1:8000/docs

CORS is wide open for Phase 1 frontend development; restrict
``allow_origins`` before any shared deployment.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.jobs import STATUS_COMPLETED, STATUS_FAILED, RunStore
from api.schemas import ConfigState, MarketState, RunRequest, T0MtmRequest, TradeSpec
from api.serializers import registry_payload, serialize_result
from pfev2.core.exceptions import PFEv2Error
from ui.utils.converters import build_config, build_market_data, build_portfolio
from ui.utils.t0_mtm import compute_t0_mtm_preview


def _build_inputs(market: MarketState, portfolio: list[TradeSpec], config: ConfigState):
    """Convert request models to pfev2 objects, mapping failures to 422.

    Validation runs synchronously at submission time so the client gets an
    immediate, specific error instead of a failed background run.
    """
    try:
        market_obj = build_market_data(market.model_dump())
        portfolio_obj = build_portfolio(
            [t.model_dump() for t in portfolio], market_obj
        )
        config_obj = build_config(config.to_state())
    except PFEv2Error as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown instrument/modifier type or missing field: {exc}",
        ) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return market_obj, portfolio_obj, config_obj


def create_app(store: RunStore | None = None) -> FastAPI:
    run_store = store if store is not None else RunStore()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        run_store.shutdown(wait=False)

    app = FastAPI(
        title="PFE-v2 API",
        version="0.1.0",
        description="REST layer over the pfev2 nested Monte Carlo PFE engine.",
        lifespan=lifespan,
    )
    app.state.run_store = run_store
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/registry")
    def registry() -> dict:
        return registry_payload()

    @app.post("/t0-mtm")
    def t0_mtm(request: T0MtmRequest) -> dict:
        # Validate first for specific 422s, then reuse the UI preview helper.
        _build_inputs(request.market, request.portfolio, request.config)
        values = compute_t0_mtm_preview(
            request.market.model_dump(),
            [t.model_dump() for t in request.portfolio],
            request.config.to_state(),
        )
        return {"per_trade_t0_mtm": values}

    @app.post("/runs", status_code=202)
    def submit_run(request: RunRequest) -> dict:
        market, portfolio, config = _build_inputs(
            request.market, request.portfolio, request.config
        )
        record = run_store.submit(portfolio, market, config, label=request.label)
        return record.summary()

    @app.get("/runs")
    def list_runs() -> list:
        return [r.summary() for r in run_store.list()]

    @app.get("/runs/{run_id}")
    def run_status(run_id: str) -> dict:
        record = run_store.get(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Unknown run id: {run_id}")
        return record.summary()

    @app.get("/runs/{run_id}/result")
    def run_result(run_id: str, include_mtm: bool = False) -> dict:
        record = run_store.get(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Unknown run id: {run_id}")
        if record.status == STATUS_FAILED:
            raise HTTPException(status_code=409, detail=record.error)
        if record.status != STATUS_COMPLETED:
            raise HTTPException(
                status_code=409,
                detail=f"Run is {record.status} (progress {record.progress:.0%})",
            )
        return serialize_result(record.result, include_mtm_matrix=include_mtm)

    return app


app = create_app()
