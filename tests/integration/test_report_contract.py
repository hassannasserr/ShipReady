import json
from pathlib import Path
from uuid import uuid4

from shipready.evidence.models import (
    ResultStatus,
    RunMetadata,
    RunReport,
    ScenarioResult,
)
from shipready.reporting.html_report import write_html_report
from shipready.reporting.json_report import write_json_report


def test_report_contract_round_trip(tmp_path: Path) -> None:
    report = RunReport(
        metadata=RunMetadata(
            run_id=uuid4(),
            config_path="configs/demo-project.yaml",
            commit_sha="0123456789abcdef",
            cleanup_status="not_required",
        ),
        results=[
            ScenarioResult(
                scenario_id="BASELINE",
                status=ResultStatus.PASSED,
                expected_behavior="HTTP 200",
                observed_behavior="HTTP 200",
                evidence=[{"name": "status_code", "value": 200}],
                reproduction_steps=["GET /health"],
            ),
            ScenarioResult(
                scenario_id="I-02",
                status=ResultStatus.NOT_VERIFIED,
                expected_behavior="Delay is measured",
                observed_behavior="Timeout prevented verification",
            ),
        ],
    )
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"

    write_json_report(report, json_path)
    write_html_report(RunReport.model_validate_json(json_path.read_text()), html_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["commit_sha"] == "0123456789abcdef"
    assert {item["status"] for item in payload["results"]} == {
        "passed",
        "not_verified",
    }
    assert "ShipReady assessment" in html_path.read_text(encoding="utf-8")
