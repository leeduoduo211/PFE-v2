"""FastAPI service exposing the pfev2 engine.

All API routes are served under the ``/api`` prefix so the service can share
one origin with the built SPA in the single-container Docker image.

Endpoints
---------
GET  /api/health              – liveness probe
GET  /api/registry            – instrument + modifier field schemas (drives forms)
POST /api/t0-mtm              – synchronous per-trade t=0 MtM preview
POST /api/runs                – validate inputs, queue a PFE run, return 202 + id
GET  /api/runs                – run history, newest first
GET  /api/runs/{id}           – status + progress for one run
GET  /api/runs/{id}/events    – Server-Sent Events stream of progress until terminal
GET  /api/runs/{id}/result    – serialized PFEResult (404/409 until completed)

If ``PFEV2_STATIC_DIR`` points at a built frontend, it is served at ``/``.
If ``PFEV2_DB_PATH`` is set, terminal runs are persisted there and reloaded
on startup.

Launch:  python3 -m uvicorn api.app:app --reload
Docs:    http://127.0.0.1:8000/docs

CORS is wide open for local frontend development; restrict ``allow_origins``
before any shared deployment. (In the single-container image the SPA shares
the API's origin, so CORS is moot there.)
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from api.jobs import STATUS_COMPLETED, STATUS_FAILED, RunStore
from api.schemas import ConfigState, MarketState, RunRequest, T0MtmRequest, TradeSpec
from api.serializers import registry_payload, serialize_result
from pfev2.core.exceptions import PFEv2Error
from ui.utils.converters import build_config, build_market_data, build_portfolio
from ui.utils.t0_mtm import compute_t0_mtm_preview

# Poll interval for the SSE generator. Short enough to feel live, long enough
# that an idle stream is cheap.
_SSE_POLL_SECONDS = 0.2


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


def _make_router(run_store: RunStore) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/registry")
    def registry() -> dict:
        return registry_payload()

    @router.post("/t0-mtm")
    def t0_mtm(request: T0MtmRequest) -> dict:
        # Validate first for specific 422s, then reuse the UI preview helper.
        _build_inputs(request.market, request.portfolio, request.config)
        values = compute_t0_mtm_preview(
            request.market.model_dump(),
            [t.model_dump() for t in request.portfolio],
            request.config.to_state(),
        )
        return {"per_trade_t0_mtm": values}

    @router.post("/runs", status_code=202)
    def submit_run(request: RunRequest) -> dict:
        market, portfolio, config = _build_inputs(
            request.market, request.portfolio, request.config
        )
        record = run_store.submit(portfolio, market, config, label=request.label)
        return record.summary()

    @router.get("/runs")
    def list_runs() -> list:
        return [r.summary() for r in run_store.list()]

    @router.get("/runs/{run_id}")
    def run_status(run_id: str) -> dict:
        record = run_store.get(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Unknown run id: {run_id}")
        return record.summary()

    @router.get("/runs/{run_id}/events")
    def run_events(run_id: str) -> StreamingResponse:
        """Stream progress as Server-Sent Events until the run is terminal.

        Emits one ``data:`` event whenever the status payload changes, and a
        final event on completion/failure, then closes. The client should
        close its EventSource on a terminal status so the browser does not
        auto-reconnect to a finished run.
        """

        async def event_stream():
            last: str | None = None
            while True:
                record = run_store.get(run_id)
                if record is None:
                    yield f"data: {json.dumps({'error': f'Unknown run id: {run_id}'})}\n\n"
                    return
                payload = json.dumps(record.summary())
                if payload != last:
                    yield f"data: {payload}\n\n"
                    last = payload
                if record.status in (STATUS_COMPLETED, STATUS_FAILED):
                    return
                await asyncio.sleep(_SSE_POLL_SECONDS)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @router.get("/runs/{run_id}/result")
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
        # Live result supports the optional MtM matrix; runs restored from disk
        # only have the serialized JSON (matrix is never persisted).
        if record.result is not None:
            return serialize_result(record.result, include_mtm_matrix=include_mtm)
        return record.result_json

    return router


def create_app(store: RunStore | None = None) -> FastAPI:
    run_store = store if store is not None else RunStore(db_path=os.environ.get("PFEV2_DB_PATH"))

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
    app.include_router(_make_router(run_store))

    # Serve the built SPA at "/" when present (the Docker image sets this).
    # Mounted last so every /api route and /docs take precedence.
    static_dir = os.environ.get("PFEV2_STATIC_DIR")
    if static_dir and os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="spa")

    return app


app = create_app()
