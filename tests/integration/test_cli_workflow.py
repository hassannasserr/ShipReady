from pathlib import Path

from typer.testing import CliRunner

from shipready.agent import cli
from shipready.evidence.models import ResultStatus, ScenarioResult


def test_baseline_workflow_writes_json_and_html(
    tmp_path: Path, monkeypatch
) -> None:
    config = Path("configs/demo-project.yaml")
    result = ScenarioResult(
        scenario_id="BASELINE",
        status=ResultStatus.PASSED,
        expected_behavior="HTTP 200",
        observed_behavior="HTTP 200",
    )
    monkeypatch.setattr(cli, "run_baseline", lambda _config: result)

    artifact_root = tmp_path / "artifacts"
    database = tmp_path / "runs.db"
    response = CliRunner().invoke(
        cli.app,
        [
            "run",
            "--engine",
            "baseline",
            "--config",
            str(config),
            "--artifacts",
            str(artifact_root),
            "--database",
            str(database),
        ],
    )

    assert response.exit_code == 0, response.stdout
    run_directory = next(artifact_root.iterdir())
    assert (run_directory / "report.json").is_file()
    assert (run_directory / "report.html").is_file()
