from typer.testing import CliRunner

from shipready.agent import cli
from shipready.agent.doctor import DoctorCheck, DoctorReport


def test_help_command_is_available() -> None:
    result = CliRunner().invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "doctor" in result.stdout


def test_doctor_command_runs_diagnostics(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "run_doctor",
        lambda: DoctorReport((DoctorCheck("Test", True, "available"),)),
    )

    result = CliRunner().invoke(cli.app, ["doctor"])

    assert result.exit_code == 0
    assert "[OK] Test: available" in result.stdout
