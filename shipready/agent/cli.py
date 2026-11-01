"""ShipReady command-line interface."""

from __future__ import annotations

import typer

from shipready.agent.doctor import run_doctor

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
