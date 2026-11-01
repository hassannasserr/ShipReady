"""ShipReady command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from shipready.agent.config import load_config
from shipready.agent.doctor import run_doctor
from shipready.agent.run_manager import RunManager
from shipready.engines.baseline.runner import run_baseline
from shipready.engines.business.client import DemoApiClient
from shipready.engines.business.duplicate_request import run_duplicate_request
from shipready.engines.business.invalid_transition import run_invalid_transition
from shipready.engines.business.invariants import run_invariants
from shipready.evidence.models import ResultStatus, RunReport
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


@app.command()
def business(
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
    """Run the baseline gate and configured business scenarios."""
    try:
        app_config = load_config(config)
    except ValueError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    manager = RunManager(artifacts, database)
    try:
        metadata, artifact_dir = manager.start(config)
        results = [run_baseline(app_config)]
        manager.repository.add_result(str(metadata.run_id), results[0])
        if results[0].status != ResultStatus.PASSED:
            manager.complete(metadata, "blocked")
            report_path = artifact_dir / "report.json"
            write_json_report(
                RunReport(metadata=metadata, results=results),
                report_path,
            )
            typer.echo(f"Run ID: {metadata.run_id}")
            typer.echo("Status: blocked (baseline did not pass)")
            typer.echo(f"Report: {report_path}")
            raise typer.Exit(code=1)

        client = DemoApiClient(
            app_config.project.base_url,
            app_config.execution.scenario_timeout_seconds,
        )
        try:
            for scenario_id in app_config.scenarios:
                if scenario_id == "B-03":
                    result = run_invariants(client, app_config.business_invariants)
                elif scenario_id == "B-01":
                    result = run_duplicate_request(client)
                elif scenario_id == "B-02":
                    result = run_invalid_transition(client)
                else:
                    continue
                results.append(result)
                manager.repository.add_result(str(metadata.run_id), result)
        finally:
            client.close()

        failed = any(
            result.status in {ResultStatus.FAILED, ResultStatus.ERROR}
            for result in results
        )
        manager.complete(metadata, "completed" if not failed else "failed")
        report_path = artifact_dir / "report.json"
        write_json_report(
            RunReport(metadata=metadata, results=results),
            report_path,
        )
        typer.echo(f"Run ID: {metadata.run_id}")
        typer.echo(
            "Results: "
            + ", ".join(
                f"{result.scenario_id}={result.status.value}" for result in results
            )
        )
        typer.echo(f"Report: {report_path}")
        if failed:
            raise typer.Exit(code=1)
    finally:
        manager.close()
