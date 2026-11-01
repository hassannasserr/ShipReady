"""ShipReady command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer
from pydantic import ValidationError

from shipready.adapters.github_adapter import RepositoryError, clone_repository
from shipready.adapters.project_detector import inspect_repository
from shipready.agent.config import load_config
from shipready.agent.doctor import run_doctor
from shipready.agent.run_manager import RunManager
from shipready.engines.baseline.runner import run_baseline
from shipready.engines.business.client import DemoApiClient
from shipready.engines.business.duplicate_request import run_duplicate_request
from shipready.engines.business.invalid_transition import run_invalid_transition
from shipready.engines.business.invariants import run_invariants
from shipready.engines.infrastructure.controller import ComposeController
from shipready.engines.infrastructure.database_outage import run_database_outage
from shipready.engines.infrastructure.dependency_latency import run_dependency_latency
from shipready.engines.infrastructure.process_restart import run_process_restart
from shipready.evidence.models import Evidence, ResultStatus, RunReport, ScenarioResult
from shipready.reporting.html_report import write_html_report
from shipready.reporting.json_report import write_json_report
from shipready.safety.cleanup import CleanupError, cleanup_workspace
from shipready.safety.policy import SafetyViolation, validate_execution_policy

app = typer.Typer(
    name="shipready",
    help="Local-first QA automation and production-readiness assessment.",
    no_args_is_help=True,
)


def _write_reports(report: RunReport, artifact_dir: Path) -> tuple[Path, Path]:
    """Write both report formats for a completed run."""
    json_path = artifact_dir / "report.json"
    html_path = artifact_dir / "report.html"
    write_json_report(report, json_path)
    write_html_report(report, html_path)
    return json_path, html_path


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


@app.command("inspect")
def inspect(
    repository: Annotated[
        str, typer.Option("--repository", help="HTTPS GitHub repository URL.")
    ],
    revision: Annotated[
        str | None,
        typer.Option("--revision", help="Branch or exact commit SHA."),
    ] = None,
    artifacts: Annotated[
        Path, typer.Option("--artifacts")
    ] = Path("artifacts"),
    database: Annotated[
        Path, typer.Option("--database")
    ] = Path("shipready.db"),
    workspace_root: Annotated[
        Path, typer.Option("--workspace-root")
    ] = Path(".shipready/workspaces"),
    keep_workspace: Annotated[
        bool, typer.Option("--keep-workspace")
    ] = False,
) -> None:
    """Clone and statically inspect a GitHub repository without running its code."""
    workspace = workspace_root / str(uuid4())
    workspace.mkdir(parents=True, exist_ok=False)
    (workspace / ".shipready-managed").write_text("managed\n", encoding="utf-8")
    repository_root = workspace / "repository"
    try:
        commit_sha = clone_repository(repository, repository_root, revision)
        inspection = inspect_repository(repository_root)
        findings = list(inspection.findings)
        status = ResultStatus.PASSED if inspection.supported else ResultStatus.FAILED
        config_path = inspection.config_path or Path("<repository inspection>")
        if inspection.supported and inspection.config_path:
            config = load_config(inspection.config_path)
            findings.extend(
                validate_execution_policy(
                    config,
                    repository_root,
                    workspace_root,
                    repository_root / "docker" / "compose.yaml",
                )
            )
        result = ScenarioResult(
            scenario_id="REPOSITORY-INSPECTION",
            status=status,
            expected_behavior=(
                "A reviewed repository is inspected without executing repository code."
            ),
            observed_behavior="; ".join(findings),
            evidence=[
                Evidence(name="repository_url", value=repository),
                Evidence(name="requested_revision", value=revision),
                Evidence(name="commit_sha", value=commit_sha),
                Evidence(name="workspace", value=str(workspace)),
            ],
            reproduction_steps=[
                "Validate HTTPS GitHub URL",
                "Clone with git --no-checkout",
                "Inspect reviewed YAML and Compose files",
            ],
        )
        manager = RunManager(artifacts, database)
        try:
            metadata, artifact_dir = manager.start(
                config_path,
                repository_url=repository,
                requested_revision=revision,
                commit_sha=commit_sha,
            )
            manager.repository.add_result(str(metadata.run_id), result)
            manager.complete(
                metadata,
                "completed" if result.status == ResultStatus.PASSED else "failed",
            )
            report_path, _ = _write_reports(
                RunReport(metadata=metadata, results=[result]),
                artifact_dir,
            )
            typer.echo(f"Run ID: {metadata.run_id}")
            typer.echo(f"Commit: {commit_sha}")
            typer.echo(f"Status: {result.status.value}")
            typer.echo(f"Report: {report_path}")
            if result.status != ResultStatus.PASSED:
                raise typer.Exit(code=1)
        finally:
            manager.close()
    except (RepositoryError, SafetyViolation, ValueError) as exc:
        typer.echo(f"Inspection rejected: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    finally:
        if not keep_workspace:
            try:
                cleanup_workspace(workspace, workspace_root)
            except CleanupError as exc:
                typer.echo(f"Cleanup error: {exc}", err=True)
                raise typer.Exit(code=1) from exc


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
        report_path, _ = _write_reports(
            RunReport(metadata=metadata, results=[result]),
            artifact_dir,
        )
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
            report_path, _ = _write_reports(
                RunReport(metadata=metadata, results=results),
                artifact_dir,
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
        report_path, _ = _write_reports(
            RunReport(metadata=metadata, results=results),
            artifact_dir,
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


@app.command()
def infrastructure(
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
    compose_file: Annotated[
        Path,
        typer.Option("--compose-file", exists=True, dir_okay=False, readable=True),
    ] = Path("docker/compose.yaml"),
) -> None:
    """Run the baseline gate and controlled infrastructure scenarios."""
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
            report_path, _ = _write_reports(
                RunReport(metadata=metadata, results=results),
                artifact_dir,
            )
            typer.echo(f"Run ID: {metadata.run_id}")
            typer.echo("Status: blocked (baseline did not pass)")
            typer.echo(f"Report: {report_path}")
            raise typer.Exit(code=1)

        client = DemoApiClient(
            app_config.project.base_url,
            app_config.execution.scenario_timeout_seconds,
        )
        controller = ComposeController(
            compose_file,
            app_config.execution.scenario_timeout_seconds,
        )
        runners = {
            "I-01": lambda: run_database_outage(
                client, controller, app_config.execution.scenario_timeout_seconds
            ),
            "I-02": lambda: run_dependency_latency(
                client,
                controller,
                2000,
                app_config.execution.scenario_timeout_seconds,
            ),
            "I-03": lambda: run_process_restart(
                client, controller, app_config.execution.scenario_timeout_seconds
            ),
        }
        try:
            for scenario_id in app_config.scenarios:
                runner = runners.get(scenario_id)
                if runner is None:
                    continue
                result = runner()
                results.append(result)
                manager.repository.add_result(str(metadata.run_id), result)
        finally:
            client.close()

        failed = any(
            result.status in {ResultStatus.FAILED, ResultStatus.ERROR}
            for result in results
        )
        manager.complete(metadata, "completed" if not failed else "failed")
        report_path, _ = _write_reports(
            RunReport(metadata=metadata, results=results),
            artifact_dir,
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


@app.command("run")
def run(
    engine: Annotated[
        str,
        typer.Option(
            "--engine",
            help="Assessment engine: baseline, business, or infrastructure.",
        ),
    ],
    config: Annotated[
        Path,
        typer.Option("--config", exists=True, dir_okay=False, readable=True),
    ] = Path("configs/demo-project.yaml"),
    artifacts: Annotated[
        Path, typer.Option("--artifacts")
    ] = Path("artifacts"),
    database: Annotated[
        Path, typer.Option("--database")
    ] = Path("shipready.db"),
    compose_file: Annotated[
        Path,
        typer.Option("--compose-file", exists=True, dir_okay=False, readable=True),
    ] = Path("docker/compose.yaml"),
) -> None:
    """Run one complete supported assessment workflow."""
    commands = {
        "baseline": lambda: baseline(config, artifacts, database),
        "business": lambda: business(config, artifacts, database),
        "infrastructure": lambda: infrastructure(
            config, artifacts, database, compose_file
        ),
    }
    selected = commands.get(engine.lower())
    if selected is None:
        typer.echo(
            "Invalid engine. Choose baseline, business, or infrastructure.",
            err=True,
        )
        raise typer.Exit(code=2)
    selected()


@app.command("report")
def report(
    source: Annotated[
        Path, typer.Argument(exists=True, dir_okay=False, readable=True)
    ],
    output: Annotated[
        Path | None, typer.Option("--output")
    ] = None,
) -> None:
    """Render an existing JSON report as a standalone HTML file."""
    try:
        report_model = RunReport.model_validate_json(source.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        typer.echo(f"Report error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    target = output or source.with_suffix(".html")
    write_html_report(report_model, target)
    typer.echo(f"HTML report: {target}")


@app.command("list-runs")
def list_runs(
    database: Annotated[
        Path, typer.Option("--database")
    ] = Path("shipready.db"),
    limit: Annotated[
        int, typer.Option("--limit", min=1, max=200)
    ] = 20,
) -> None:
    """List recent locally persisted runs."""
    manager = RunManager(Path("artifacts"), database)
    try:
        rows = manager.repository.list_runs(limit)
    finally:
        manager.close()
    if not rows:
        typer.echo("No runs found.")
        return
    for row in rows:
        commit = row["commit_sha"] or "-"
        typer.echo(
            f"{row['run_id']}  {row['status']}  "
            f"{row['started_at']}  commit={commit}"
        )
