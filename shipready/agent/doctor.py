"""Checks for the tools required to run ShipReady locally."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Final

REQUIRED_PYTHON_MODULES: Final[tuple[str, ...]] = (
    "httpx",
    "pydantic",
    "typer",
)


@dataclass(frozen=True)
class DoctorCheck:
    """Result of one environment diagnostic."""

    name: str
    available: bool
    message: str


@dataclass(frozen=True)
class DoctorReport:
    """Complete environment diagnostic report."""

    checks: tuple[DoctorCheck, ...]

    @property
    def is_healthy(self) -> bool:
        """Return whether every required diagnostic passed."""
        return all(check.available for check in self.checks)


def _check_python() -> DoctorCheck:
    version = sys.version_info
    available = version >= (3, 11)
    version_text = f"{version.major}.{version.minor}.{version.micro}"
    message = (
        f"Python {version_text} meets the >=3.11 requirement."
        if available
        else f"Python {version_text} is too old; install Python 3.11 or later."
    )
    return DoctorCheck("Python", available, message)


def _check_python_modules() -> DoctorCheck:
    missing = [
        module
        for module in REQUIRED_PYTHON_MODULES
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        return DoctorCheck(
            "Python dependencies",
            False,
            "Missing "
            + ", ".join(missing)
            + "; run `python -m pip install -e \".[dev]\"`.",
        )
    return DoctorCheck(
        "Python dependencies",
        True,
        "Required runtime packages are importable.",
    )


def _check_command(
    name: str, command: tuple[str, ...], install_hint: str
) -> DoctorCheck:
    executable = shutil.which(command[0])
    if executable is None:
        return DoctorCheck(name, False, f"Not found; {install_hint}")
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return DoctorCheck(name, False, f"Could not run {name}: {exc}")
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "the command returned a non-zero status"
        return DoctorCheck(name, False, f"Unavailable: {detail}")
    version = (completed.stdout.strip() or completed.stderr.strip()).splitlines()
    version_text = version[0] if version else "available"
    return DoctorCheck(name, True, version_text)


def run_doctor() -> DoctorReport:
    """Run all local prerequisite checks without changing the environment."""
    checks = (
        _check_python(),
        _check_python_modules(),
        _check_command("Git", ("git", "--version"), "install Git"),
        _check_command("Docker", ("docker", "--version"), "install Docker Desktop"),
        _check_command(
            "Docker Compose",
            ("docker", "compose", "version"),
            "install Docker Compose through Docker Desktop",
        ),
    )
    return DoctorReport(checks)
