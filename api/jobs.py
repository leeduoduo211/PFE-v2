"""In-process run store for asynchronous PFE computations.

A ``RunStore`` owns a small thread pool and a registry of ``RunRecord``s.
``compute_pfe`` releases the GIL inside NumPy, so threads give real
concurrency without a broker; this is deliberately the simplest thing that
works for single-desk use. If multiple concurrent users ever matter, this
module is the seam to swap for Celery/Redis without touching the endpoints.
"""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from pfev2.risk.pfe import compute_pfe

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


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
    result: object | None = None  # PFEResult once completed

    def summary(self) -> dict:
        """JSON-safe status payload (excludes the result arrays)."""
        done = self.status == STATUS_COMPLETED
        return {
            "run_id": self.run_id,
            "label": self.label,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "peak_pfe": self.result.peak_pfe if done else None,
            "computation_time": self.result.computation_time if done else None,
        }


class RunStore:
    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="pfe-run"
        )
        self._runs: dict[str, RunRecord] = {}
        self._lock = threading.Lock()

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
            record.progress = 1.0
            record.status = STATUS_COMPLETED
        finally:
            record.finished_at = time.time()

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
