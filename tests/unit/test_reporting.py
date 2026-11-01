import json
from pathlib import Path
from uuid import uuid4

from shipready.evidence.models import (
    ResultStatus,
    RunMetadata,
    RunReport,
    ScenarioResult,
)
from shipready.reporting.json_report import write_json_report


def test_json_report_contains_result(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report = RunReport(
        metadata=RunMetadata(run_id=uuid4(), config_path="config.yaml"),
        results=[
            ScenarioResult(
                scenario_id="BASELINE",
                status=ResultStatus.PASSED,
                expected_behavior="HTTP 200",
                observed_behavior="HTTP 200",
            )
        ],
    )

    write_json_report(report, report_path)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["status"] == "passed"
