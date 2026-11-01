"""Non-executing inspection of a checked-out project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shipready.agent.config import AppConfig, load_config


@dataclass(frozen=True)
class InspectionReport:
    supported: bool
    config_path: Path | None
    findings: tuple[str, ...]


def inspect_repository(repository_root: Path) -> InspectionReport:
    """Inspect known files only; never import or execute repository code."""
    candidates = (
        repository_root / "shipready.yaml",
        repository_root / "configs" / "shipready.yaml",
        repository_root / "configs" / "demo-project.yaml",
    )
    config_path = next((path for path in candidates if path.is_file()), None)
    if config_path is None:
        return InspectionReport(
            supported=False,
            config_path=None,
            findings=("No reviewed ShipReady configuration was found.",),
        )
    try:
        config: AppConfig = load_config(config_path)
    except ValueError as exc:
        return InspectionReport(
            supported=False,
            config_path=config_path,
            findings=(f"Configuration rejected: {exc}",),
        )
    compose = repository_root / "docker" / "compose.yaml"
    findings = (
        f"Reviewed configuration: {config_path.relative_to(repository_root)}",
        f"Adapter: {config.project.adapter}",
        (
            "Docker Compose file found for static safety inspection."
            if compose.is_file()
            else "No Docker Compose file found; execution is not approved."
        ),
    )
    return InspectionReport(
        supported=compose.is_file(),
        config_path=config_path,
        findings=findings,
    )
