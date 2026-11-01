"""Shared result and run metadata models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResultStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    NOT_VERIFIED = "not_verified"
    SKIPPED = "skipped"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: Any


class ScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    status: ResultStatus
    expected_behavior: str
    observed_behavior: str
    evidence: list[Evidence] = Field(default_factory=list)
    reproduction_steps: list[str] = Field(default_factory=list)
    duration_ms: float | None = None


class RunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    completed_at: datetime | None = None
    status: str = "created"
    config_path: str
    repository_url: str | None = None
    requested_revision: str | None = None
    commit_sha: str | None = None
    cleanup_status: str | None = None
    safety_warnings: list[str] = Field(default_factory=list)


class RunReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: RunMetadata
    results: list[ScenarioResult] = Field(default_factory=list)
