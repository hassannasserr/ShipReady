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
    config_path TEXT NOT NULL,
    repository_url TEXT,
    requested_revision TEXT,
    commit_sha TEXT
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
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(runs)").fetchall()
    }
    for column in ("repository_url", "requested_revision", "commit_sha"):
        if column not in columns:
            connection.execute(f"ALTER TABLE runs ADD COLUMN {column} TEXT")
    connection.commit()
    return connection
