"""Cleanup for resources owned by one ShipReady run."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from stat import S_IWRITE
from time import sleep


class CleanupError(RuntimeError):
    """Raised when run-owned cleanup cannot be completed."""


def cleanup_workspace(workspace: Path, managed_root: Path) -> None:
    """Remove only a directory beneath the managed root."""
    resolved_workspace = workspace.resolve()
    resolved_root = managed_root.resolve()
    if (
        resolved_workspace == resolved_root
        or resolved_root not in resolved_workspace.parents
    ):
        raise CleanupError("refusing to clean a workspace outside the managed root")
    if not (resolved_workspace / ".shipready-managed").is_file():
        raise CleanupError("refusing to clean an unmarked workspace")
    last_error: OSError | None = None
    for _ in range(3):
        try:
            shutil.rmtree(resolved_workspace, onerror=_make_writable)
            return
        except OSError as exc:
            last_error = exc
            sleep(0.25)
    raise CleanupError(f"workspace cleanup failed: {last_error}")


def _make_writable(
    function: object,
    path: str,
    _exc_info: object,
) -> None:
    os.chmod(path, S_IWRITE)
    if callable(function):
        function(path)
