import json
from pathlib import Path
from uuid import uuid4

from shipready.evidence.collector import redact
from shipready.evidence.models import (
    ResultStatus,
    RunMetadata,
    RunReport,
    ScenarioResult,
)
from shipready.reporting.html_report import write_html_report
from shipready.reporting.json_report import write_json_report


def _report() -> RunReport:
    return RunReport(
        metadata=RunMetadata(run_id=uuid4(), config_path="config.yaml"),
        results=[
            ScenarioResult(
                scenario_id="I-02",
                status=ResultStatus.NOT_VERIFIED,
                expected_behavior="<expected>",
                observed_behavior="Bearer abc123",
                evidence=[],
            )
        ],
    )


def test_reports_are_generated_and_html_is_escaped(tmp_path: Path) -> None:
    report = _report()
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"

    write_json_report(report, json_path)
    write_html_report(report, html_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["status"] == "not_verified"
    content = html_path.read_text(encoding="utf-8")
    assert "&lt;expected&gt;" in content
    assert "<expected>" not in content
    assert "Bearer [REDACTED]" in content


def test_nested_secret_values_are_redacted() -> None:
    assert redact({"Authorization": "secret", "nested": {"token": "value"}}) == {
        "Authorization": "[REDACTED]",
        "nested": {"token": "[REDACTED]"},
    }
    assert redact("token=hidden password: secret") == (
        "token=[REDACTED] password: [REDACTED]"
    )
