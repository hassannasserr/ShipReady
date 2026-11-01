from pathlib import Path

from shipready.agent.run_manager import RunManager
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def test_run_manager_persists_run_and_result(tmp_path: Path) -> None:
    manager = RunManager(tmp_path / "artifacts", tmp_path / "runs.db")
    try:
        metadata, artifact_dir = manager.start(Path("config.yaml"))
        result = ScenarioResult(
            scenario_id="BASELINE",
            status=ResultStatus.PASSED,
            expected_behavior="HTTP 200",
            observed_behavior="HTTP 200: healthy",
            evidence=[Evidence(name="status_code", value=200)],
        )
        manager.repository.add_result(str(metadata.run_id), result)
        manager.complete(metadata, "completed")

        assert artifact_dir.is_dir()
        assert manager.repository.count_results(str(metadata.run_id)) == 1
    finally:
        manager.close()
