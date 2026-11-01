"""Validated configuration loading for approved local applications."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_SCENARIOS = {"I-01", "I-02", "I-03", "B-01", "B-02", "B-03"}
SUPPORTED_INVARIANTS = {
    "payment_has_operation_id",
    "payment_is_associated_with_order",
    "one_logical_payment_recorded",
    "paid_order_matches_success",
}


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    adapter: str
    base_url: str

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("base_url must use http://localhost or http://127.0.0.1")
        if parsed.username or parsed.password:
            raise ValueError("base_url must not contain credentials")
        return value.rstrip("/")


class HealthCheckConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(pattern=r"^/")
    expected_status: int = Field(ge=100, le=599)
    timeout_seconds: float = Field(gt=0, le=60)


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    disposable_test_database: bool

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value != "mongodb":
            raise ValueError("only mongodb is supported")
        return value

    @field_validator("disposable_test_database")
    @classmethod
    def validate_disposable(cls, value: bool) -> bool:
        if not value:
            raise ValueError("the test database must be disposable")
        return value


class ExecutionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_run_seconds: float = Field(gt=0, le=3600)
    scenario_timeout_seconds: float = Field(gt=0, le=300)
    allow_external_network: bool

    @field_validator("allow_external_network")
    @classmethod
    def validate_network(cls, value: bool) -> bool:
        if value:
            raise ValueError("external network access must be disabled")
        return value


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: ProjectConfig
    health_check: HealthCheckConfig
    database: DatabaseConfig
    execution: ExecutionConfig
    scenarios: list[str] = Field(min_length=1)
    business_invariants: list[str] = Field(default_factory=list)

    @field_validator("scenarios")
    @classmethod
    def validate_scenarios(cls, values: list[str]) -> list[str]:
        unsupported = sorted(set(values) - SUPPORTED_SCENARIOS)
        if unsupported:
            raise ValueError(f"unsupported scenario IDs: {', '.join(unsupported)}")
        return values

    @field_validator("business_invariants")
    @classmethod
    def validate_invariants(cls, values: list[str]) -> list[str]:
        unsupported = sorted(set(values) - SUPPORTED_INVARIANTS)
        if unsupported:
            raise ValueError(f"unsupported invariant IDs: {', '.join(unsupported)}")
        return values


def load_config(path: Path) -> AppConfig:
    """Load and validate a YAML configuration file."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read configuration {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a YAML mapping")
    try:
        return AppConfig.model_validate(raw)
    except ValueError as exc:
        raise ValueError(f"invalid configuration: {exc}") from exc
