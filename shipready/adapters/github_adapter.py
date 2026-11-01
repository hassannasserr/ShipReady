"""Safe GitHub repository validation and cloning."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

GITHUB_URL = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?$"
)
REVISION = re.compile(r"^[A-Za-z0-9._/-]+$")


class RepositoryError(ValueError):
    """Raised when a repository cannot be safely selected or cloned."""


def validate_github_url(value: str) -> str:
    """Return a normalized public GitHub URL or reject it."""
    parsed = urlparse(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RepositoryError("repository URL must not contain credentials or URL data")
    match = GITHUB_URL.fullmatch(value.rstrip("/"))
    if not match:
        raise RepositoryError("repository URL must be an HTTPS GitHub repository URL")
    return f"https://github.com/{match.group(1)}/{match.group(2)}.git"


def _validate_revision(revision: str) -> None:
    if (
        not revision
        or not REVISION.fullmatch(revision)
        or revision.startswith(("/", "-"))
    ):
        raise RepositoryError("revision contains unsupported characters")


def _is_commit_revision(revision: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", revision))


def _run_git(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RepositoryError(f"git command could not be completed: {exc}") from exc


def clone_repository(
    repository_url: str,
    destination: Path,
    revision: str | None = None,
) -> str:
    """Clone without executing repository code and return the resolved commit SHA."""
    normalized_url = validate_github_url(repository_url)
    if revision is not None:
        _validate_revision(revision)
    if destination.exists() and any(destination.iterdir()):
        raise RepositoryError("clone destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    command = ["git", "clone", "--no-checkout"]
    if not revision or not _is_commit_revision(revision):
        command.extend(["--depth", "1"])
    if revision and not _is_commit_revision(revision):
        command.extend(["--branch", revision])
    command.extend([normalized_url, str(destination)])
    cloned = _run_git(command, 300)
    if cloned.returncode != 0:
        detail = cloned.stderr.strip() or cloned.stdout.strip()
        raise RepositoryError(f"git clone failed: {detail}")

    checkout_target = revision or "HEAD"
    checkout = _run_git(
        ["git", "-C", str(destination), "checkout", "--detach", checkout_target],
        60,
    )
    resolved = _run_git(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        60,
    )
    if checkout.returncode != 0 or resolved.returncode != 0:
        detail = checkout.stderr.strip() or resolved.stderr.strip()
        raise RepositoryError(f"requested revision could not be checked out: {detail}")
    return resolved.stdout.strip()
