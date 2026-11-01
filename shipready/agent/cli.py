"""ShipReady command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from shipready.agent.config import load_config
from shipready.agent.doctor import run_doctor
from shipready.agent.run_manager import RunManager
from shipready.engines.baseline.runner import run_baseline
from shipready.evidence.models import RunReport
from shipready.reporting.json_report import write_json_report

app = typer.Typer(
    name="shipready",
    help="Local-first QA automation and production-readiness assessment.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Run ShipReady commands."""


@app.command()
def doctor() -> None:
    """Check the local environment and report actionable diagnostics."""
    report = run_doctor()
    for check in report.checks:
        status = "OK" if check.available else "MISSING"
        typer.echo(f"[{status}] {check.name}: {check.message}")

    if not report.is_healthy:
        raise typer.Exit(code=1)


@app.command()
def baseline(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = Path("configs/demo-project.yaml"),
    artifacts: Annotated[
        Path, typer.Option("--artifacts")
    ] = Path("artifacts"),
    database: Annotated[
        Path, typer.Option("--database")
    ] = Path("shipready.db"),
) -> None:
    """Run the baseline health check and persist its report."""
    try:
        app_config = load_config(config)
    except ValueError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    manager = RunManager(artifacts, database)
    try:
        metadata, artifact_dir = manager.start(config)
        result = run_baseline(app_config)
        manager.repository.add_result(str(metadata.run_id), result)
        status = "completed" if result.status == "passed" else "blocked"
        manager.complete(metadata, status)
        report_path = artifact_dir / "report.json"
        write_json_report(RunReport(metadata=metadata, results=[result]), report_path)
        typer.echo(f"Run ID: {metadata.run_id}")
        typer.echo(f"Status: {result.status.value}")
        typer.echo(f"Report: {report_path}")
        if result.status != "passed":
            raise typer.Exit(code=1)
    finally:
        manager.close()
