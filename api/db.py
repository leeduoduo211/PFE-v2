"""SQLite persistence for run history.

Deliberately tiny: one table, connection-per-operation in WAL mode (safe
across the RunStore's worker threads without a shared connection). Only
terminal runs (completed/failed) are persisted — a run interrupted by a
restart has lost its in-flight thread and result, so it is not resurrected
as a stuck "running" row.
"""

from __future__ import annotations

import json
import sqlite3

_COLUMNS = (
    "run_id",
    "label",
    "status",
    "progress",
    "submitted_at",
    "started_at",
    "finished_at",
    "error",
    "peak_pfe",
    "computation_time",
    "result_json",
)


def _connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: str) -> None:
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id           TEXT PRIMARY KEY,
                label            TEXT,
                status           TEXT NOT NULL,
                progress         REAL NOT NULL,
                submitted_at     REAL NOT NULL,
                started_at       REAL,
                finished_at      REAL,
                error            TEXT,
                peak_pfe         REAL,
                computation_time REAL,
                result_json      TEXT
            )
            """
        )


def upsert_run(path: str, row: dict) -> None:
    """Insert or replace one run. ``row['result_json']`` is a dict or None."""
    values = dict(row)
    rj = values.get("result_json")
    values["result_json"] = json.dumps(rj) if rj is not None else None
    placeholders = ", ".join("?" for _ in _COLUMNS)
    with _connect(path) as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO runs ({', '.join(_COLUMNS)}) VALUES ({placeholders})",
            tuple(values.get(c) for c in _COLUMNS),
        )


def load_runs(path: str) -> list[dict]:
    """All persisted runs as dicts, with ``result_json`` decoded back to a dict."""
    with _connect(path) as conn:
        rows = conn.execute("SELECT * FROM runs").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["result_json"] = json.loads(d["result_json"]) if d["result_json"] else None
        out.append(d)
    return out
