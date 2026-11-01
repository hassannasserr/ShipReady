"""Explicit approval boundary for executing reviewed target code."""

from __future__ import annotations

from shipready.safety.policy import SafetyViolation


def require_execution_approval(approved: bool) -> None:
    """Reject target execution unless the user explicitly approved it."""
    if not approved:
        raise SafetyViolation(
            "target execution requires explicit approval; "
            "inspection did not execute code"
        )
