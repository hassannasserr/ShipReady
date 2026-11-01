"""Safe controls for the approved local Docker Compose environment."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class ComposeController:
    """Run a small allowlist of non-destructive Compose operations."""

    APPROVED_SERVICES = {"app", "mongo"}
    PROJECT_NAME = "shipready-demo"

    def __init__(self, compose_file: Path, timeout: float) -> None:
        self.compose_file = compose_file
        self.timeout = timeout

    def _run(self, *args: str, environment: dict[str, str] | None = None) -> str:
        command = [
            "docker",
            "compose",
            "-p",
            self.PROJECT_NAME,
            "-f",
            str(self.compose_file),
            *args,
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=environment,
            )
        except subprocess.TimeoutExpired as exc:
            command_text = " ".join(command)
            raise RuntimeError(f"Compose command timed out: {command_text}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"Compose command failed: {' '.join(command)}: {detail}")
        return completed.stdout.strip()

    def verify_project_ownership(self) -> None:
        """Ensure Compose targets only the fixed ShipReady project."""
        configured = set(self._run("config", "--services").splitlines())
        if configured != self.APPROVED_SERVICES:
            raise RuntimeError(
                "Compose project does not define exactly the approved "
                "app and mongo services"
            )
        owned = set(self._run("ps", "--all", "--services").splitlines())
        if owned and owned != self.APPROVED_SERVICES:
            raise RuntimeError(
                "Compose project contains services outside the approved allowlist"
            )
        if not owned:
            raise RuntimeError(
                f"Compose project {self.PROJECT_NAME!r} is not running or "
                "owned by this run"
            )

    def stop(self, service: str) -> None:
        if service not in self.APPROVED_SERVICES:
            raise ValueError(f"service is not approved: {service}")
        self._run("stop", service)

    def start(self, service: str) -> None:
        if service not in self.APPROVED_SERVICES:
            raise ValueError(f"service is not approved: {service}")
        self._run("start", service)

    def restart(self, service: str) -> None:
        if service not in self.APPROVED_SERVICES:
            raise ValueError(f"service is not approved: {service}")
        self._run("restart", service)

    def set_delay(self, milliseconds: int) -> None:
        if milliseconds < 0 or milliseconds > 30_000:
            raise ValueError("delay must be between 0 and 30000 milliseconds")
        environment = os.environ.copy()
        if milliseconds:
            environment["DEMO_DELAY_MS"] = str(milliseconds)
        else:
            environment.pop("DEMO_DELAY_MS", None)
        self._run("up", "-d", "--force-recreate", "app", environment=environment)
