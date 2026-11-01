"""Persistence operations for runs and scenario results."""

from __future__ import annotations

import json
import sqlite3

from shipready.evidence.models import RunMetadata, ScenarioResult


class RunRepository:
    """Persist run metadata and results in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_run(self, metadata: RunMetadata) -> None:
        self.connection.execute(
            """
            INSERT INTO runs(
                run_id, started_at, completed_at, status, config_path,
                repository_url, requested_revision, commit_sha,
                cleanup_status, safety_warnings_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(metadata.run_id),
                metadata.started_at.isoformat(),
                metadata.completed_at.isoformat()
                if metadata.completed_at
                else None,
                metadata.status,
                metadata.config_path,
                metadata.repository_url,
                metadata.requested_revision,
                metadata.commit_sha,
                metadata.cleanup_status,
                json.dumps(metadata.safety_warnings),
            ),
        )
        self.connection.commit()

    def update_run(self, metadata: RunMetadata) -> None:
        self.connection.execute(
            """
            UPDATE runs
            SET completed_at = ?, status = ?, config_path = ?,
                cleanup_status = ?, safety_warnings_json = ?
            WHERE run_id = ?
            """,
            (
                metadata.completed_at.isoformat()
                if metadata.completed_at
                else None,
                metadata.status,
                metadata.config_path,
                metadata.cleanup_status,
                json.dumps(metadata.safety_warnings),
                str(metadata.run_id),
            ),
        )
        self.connection.commit()

    def add_result(self, run_id: str, result: ScenarioResult) -> None:
        self.connection.execute(
            """
            INSERT INTO scenario_results(
                run_id, scenario_id, status, expected_behavior, observed_behavior,
                evidence_json, reproduction_steps_json, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                result.scenario_id,
                result.status.value,
                result.expected_behavior,
                result.observed_behavior,
                json.dumps(
                    [item.model_dump(mode="json") for item in result.evidence]
                ),
                json.dumps(result.reproduction_steps),
                result.duration_ms,
            ),
        )
        self.connection.commit()

    def count_results(self, run_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM scenario_results WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def list_runs(self, limit: int = 50) -> list[dict[str, object]]:
        """Return recent local runs for CLI history."""
        rows = self.connection.execute(
            """
            SELECT run_id, started_at, completed_at, status, config_path,
                   repository_url, requested_revision, commit_sha
            FROM runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "run_id": row[0],
                "started_at": row[1],
                "completed_at": row[2],
                "status": row[3],
                "config_path": row[4],
                "repository_url": row[5],
                "requested_revision": row[6],
                "commit_sha": row[7],
            }
            for row in rows
        ]
