"""JSON report serialization."""

from __future__ import annotations

import json
from pathlib import Path

from shipready.evidence.collector import redact
from shipready.evidence.models import RunReport


def write_json_report(report: RunReport, path: Path) -> None:
    """Write a complete run report as readable JSON."""
    path.write_text(
        json.dumps(redact(report.model_dump(mode="json")), indent=2) + "\n",
        encoding="utf-8",
    )
