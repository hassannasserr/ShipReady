"""Static safety policy checks for reviewed repositories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from shipready.agent.config import AppConfig


class SafetyViolation(ValueError):
    """Raised when a project violates a mandatory execution boundary."""


def validate_workspace(repository_root: Path, managed_root: Path) -> None:
    """Ensure the target is inside the ShipReady-managed workspace."""
    root = repository_root.resolve()
    managed = managed_root.resolve()
    if root == managed or managed not in root.parents:
        raise SafetyViolation("repository must be inside the managed workspace")


def inspect_compose_safety(compose_path: Path) -> tuple[str, ...]:
    """Inspect Compose YAML without starting containers."""
    try:
        raw: Any = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SafetyViolation(f"Compose file could not be inspected: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("services"), dict):
        raise SafetyViolation("Compose file must define a services mapping")
    services = raw["services"]
    findings: list[str] = []
    for name, service in services.items():
        if not isinstance(service, dict):
            raise SafetyViolation(f"service {name} is not a mapping")
        if service.get("privileged") is True:
            raise SafetyViolation(f"service {name} requests privileged mode")
        if service.get("network_mode") in {"host", "none"}:
            raise SafetyViolation(f"service {name} uses unsupported network mode")
        if service.get("privileged") is False and "cap_add" in service:
            raise SafetyViolation(f"service {name} declares extra capabilities")
        volumes = service.get("volumes", [])
        if isinstance(volumes, list) and any(
            "/var/run/docker.sock" in str(volume).lower() for volume in volumes
        ):
            raise SafetyViolation(f"service {name} mounts the Docker socket")
        ports = service.get("ports", [])
        if name == "mongo" and ports:
            raise SafetyViolation("mongo must not publish host ports")
        if name == "app" and not any(
            str(port).startswith("127.0.0.1:") for port in (ports or [])
        ):
            raise SafetyViolation("app must publish only on the loopback interface")
        findings.append(f"Inspected service: {name}")
    networks = raw.get("networks")
    internal_network = (
        networks.get("demo-internal") if isinstance(networks, dict) else None
    )
    if not isinstance(internal_network, dict) or not internal_network.get("internal"):
        raise SafetyViolation("Compose file must define an internal demo network")
    if set(services) != {"app", "mongo"}:
        raise SafetyViolation("Compose file must contain only app and mongo services")
    return tuple(findings)


def validate_execution_policy(
    config: AppConfig,
    repository_root: Path,
    managed_root: Path,
    compose_path: Path,
) -> tuple[str, ...]:
    """Run all mandatory static checks before target execution."""
    validate_workspace(repository_root, managed_root)
    if config.execution.allow_external_network:
        raise SafetyViolation("external network access must be disabled")
    if not config.database.disposable_test_database:
        raise SafetyViolation("the target database must be disposable")
    return inspect_compose_safety(compose_path)
