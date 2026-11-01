"""SQLite schema and connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    config_path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scenario_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    scenario_id TEXT NOT NULL,
    status TEXT NOT NULL,
    expected_behavior TEXT NOT NULL,
    observed_behavior TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    reproduction_steps_json TEXT NOT NULL,
    duration_ms REAL
);
"""


def initialize_database(path: Path) -> sqlite3.Connection:
    """Create the database schema and return an open connection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    connection.commit()
    return connection
