"""In-process run store for asynchronous PFE computations.

A ``RunStore`` owns a small thread pool and a registry of ``RunRecord``s.
``compute_pfe`` releases the GIL inside NumPy, so threads give real
concurrency without a broker; this is deliberately the simplest thing that
works for single-desk use. If multiple concurrent users ever matter, this
module is the seam to swap for Celery/Redis without touching the endpoints.

When constructed with ``db_path``, terminal runs are persisted to SQLite via
``api.db`` and reloaded on startup, so run history survives a restart.
"""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from api import db
from api.serializers import serialize_result
from pfev2.risk.pfe import compute_pfe

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
_TERMINAL = (STATUS_COMPLETED, STATUS_FAILED)


@dataclass
class RunRecord:
    run_id: str
    label: str | None = None
    status: str = STATUS_QUEUED
    progress: float = 0.0
    submitted_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    result: object | None = None  # live PFEResult; None for runs restored from disk
    result_json: dict | None = None  # serialized result (no MtM matrix); persisted
    peak_pfe: float | None = None
    computation_time: float | None = None

    def summary(self) -> dict:
        """JSON-safe status payload (excludes the result arrays)."""
        return {
            "run_id": self.run_id,
            "label": self.label,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "peak_pfe": self.peak_pfe,
            "computation_time": self.computation_time,
        }

    def to_row(self) -> dict:
        return {
            "run_id": self.run_id,
            "label": self.label,
            "status": self.status,
            "progress": self.progress,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "peak_pfe": self.peak_pfe,
            "computation_time": self.computation_time,
            "result_json": self.result_json,
        }

    @classmethod
    def from_row(cls, row: dict) -> RunRecord:
        return cls(
            run_id=row["run_id"],
            label=row["label"],
            status=row["status"],
            progress=row["progress"],
            submitted_at=row["submitted_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            error=row["error"],
            result=None,
            result_json=row["result_json"],
            peak_pfe=row["peak_pfe"],
            computation_time=row["computation_time"],
        )


class RunStore:
    def __init__(self, max_workers: int = 2, db_path: str | None = None):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="pfe-run"
        )
        self._runs: dict[str, RunRecord] = {}
        self._lock = threading.Lock()
        self._db_path = db_path
        if db_path:
            db.init_db(db_path)
            for row in db.load_runs(db_path):
                rec = RunRecord.from_row(row)
                self._runs[rec.run_id] = rec

    def submit(self, portfolio, market, config, label=None) -> RunRecord:
        """Queue a run. Inputs must already be validated pfev2 objects."""
        record = RunRecord(
            run_id=uuid.uuid4().hex[:12],
            label=label,
            submitted_at=time.time(),
        )
        with self._lock:
            self._runs[record.run_id] = record
        self._executor.submit(self._execute, record, portfolio, market, config)
        return record

    def _execute(self, record: RunRecord, portfolio, market, config) -> None:
        record.status = STATUS_RUNNING
        record.started_at = time.time()

        def on_progress(p: float) -> None:
            record.progress = float(p)

        try:
            result = compute_pfe(
                portfolio, market, config,
                on_progress=on_progress,
                per_trade_detail=True,
            )
        except Exception as exc:  # surfaced via the status endpoint
            record.error = f"{type(exc).__name__}: {exc}"
            record.status = STATUS_FAILED
        else:
            record.result = result
            record.result_json = serialize_result(result)
            record.peak_pfe = result.peak_pfe
            record.computation_time = result.computation_time
            record.progress = 1.0
            record.status = STATUS_COMPLETED
        finally:
            record.finished_at = time.time()
            self._persist(record)

    def _persist(self, record: RunRecord) -> None:
        if self._db_path and record.status in _TERMINAL:
            db.upsert_run(self._db_path, record.to_row())

    def get(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def list(self) -> list[RunRecord]:
        """All runs, newest first."""
        with self._lock:
            records = list(self._runs.values())
        return sorted(records, key=lambda r: r.submitted_at, reverse=True)

    def shutdown(self, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait)
