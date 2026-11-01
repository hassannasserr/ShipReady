"""Run lifecycle and artifact directory management."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from shipready.evidence.models import RunMetadata
from shipready.storage.database import initialize_database
from shipready.storage.repositories import RunRepository


class RunManager:
    """Create and complete isolated ShipReady runs."""

    def __init__(self, artifacts_root: Path, database_path: Path) -> None:
        self.artifacts_root = artifacts_root
        self.database_path = database_path
        self.connection = initialize_database(database_path)
        self.repository = RunRepository(self.connection)

    def start(
        self,
        config_path: Path,
        *,
        repository_url: str | None = None,
        requested_revision: str | None = None,
        commit_sha: str | None = None,
    ) -> tuple[RunMetadata, Path]:
        metadata = RunMetadata(
            config_path=str(config_path),
            status="running",
            repository_url=repository_url,
            requested_revision=requested_revision,
            commit_sha=commit_sha,
        )
        artifact_dir = self.artifacts_root / str(metadata.run_id)
        artifact_dir.mkdir(parents=True, exist_ok=False)
        self.repository.create_run(metadata)
        return metadata, artifact_dir

    def complete(self, metadata: RunMetadata, status: str) -> None:
        metadata.completed_at = datetime.now(UTC)
        metadata.status = status
        self.repository.update_run(metadata)

    def close(self) -> None:
        self.connection.close()
