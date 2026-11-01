"""Shared helpers for infrastructure scenarios."""

from __future__ import annotations

from time import monotonic, perf_counter, sleep

import httpx

from shipready.engines.business.client import DemoApiClient
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def wait_for_health(client: DemoApiClient, timeout: float) -> bool:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        try:
            response = client.client.get("/health")
            if response.status_code == 200:
                return True
        except (httpx.HTTPError, OSError):
            pass
        sleep(0.25)
    return False


def error_result(
    scenario_id: str,
    expected: str,
    observed: str,
    evidence: list[Evidence],
    steps: list[str],
    started: float,
) -> ScenarioResult:
    return ScenarioResult(
        scenario_id=scenario_id,
        status=ResultStatus.ERROR,
        expected_behavior=expected,
        observed_behavior=observed,
        evidence=evidence,
        reproduction_steps=steps,
        duration_ms=(perf_counter() - started) * 1000,
    )
