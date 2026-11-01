"""Standalone, escaped HTML report generation."""

from __future__ import annotations

import html
import json
from pathlib import Path

from shipready.evidence.collector import redact
from shipready.evidence.models import RunReport


def _text(value: object) -> str:
    return html.escape(str(value))


def write_html_report(report: RunReport, path: Path) -> None:
    """Write a self-contained report without interpreting report content."""
    payload = redact(report.model_dump(mode="json"))
    metadata = payload["metadata"]
    cards: list[str] = []
    for result in payload["results"]:
        evidence = "".join(
            f"<li><b>{_text(item['name'])}</b>: "
            f"{_text(json.dumps(item['value']))}</li>"
            for item in result["evidence"]
        )
        steps = "".join(
            f"<li>{_text(step)}</li>" for step in result["reproduction_steps"]
        )
        cards.append(
            "<article>"
            f"<h2>{_text(result['scenario_id'])} "
            f"<span class='status'>{_text(result['status'])}</span></h2>"
            f"<p><b>Expected:</b> {_text(result['expected_behavior'])}</p>"
            f"<p><b>Observed:</b> {_text(result['observed_behavior'])}</p>"
            f"<h3>Evidence</h3><ul>{evidence}</ul>"
            f"<h3>Reproduction</h3><ol>{steps}</ol>"
            "</article>"
        )
    warnings = "".join(
        f"<li>{_text(item)}</li>" for item in metadata["safety_warnings"]
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>ShipReady report</title>
<style>body{{font-family:system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}}
article{{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}}
.status{{font-size:.8em;background:#eee;padding:.2rem .5rem;border-radius:4px}}
li{{margin:.3rem 0}} .warning{{color:#8a4b00}}</style></head>
<body><h1>ShipReady assessment</h1>
<p><b>Run:</b> {_text(metadata["run_id"])} |
<b>Status:</b> {_text(metadata["status"])}</p>
<p><b>Commit:</b> {_text(metadata.get("commit_sha") or "not recorded")}</p>
<p><b>Cleanup:</b> {_text(metadata.get("cleanup_status") or "not recorded")}</p>
<h2>Safety warnings</h2><ul class="warning">{warnings or "<li>None</li>"}</ul>
{"".join(cards)}</body></html>"""
    path.write_text(document, encoding="utf-8")
