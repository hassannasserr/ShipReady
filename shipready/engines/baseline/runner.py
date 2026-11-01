"""Baseline health and behavior checks."""

from __future__ import annotations

from time import perf_counter

import httpx

from shipready.agent.config import AppConfig
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def run_baseline(config: AppConfig) -> ScenarioResult:
    """Check the configured application health endpoint."""
    url = f"{config.project.base_url}{config.health_check.path}"
    started = perf_counter()
    try:
        response = httpx.get(url, timeout=config.health_check.timeout_seconds)
    except httpx.HTTPError as exc:
        duration_ms = (perf_counter() - started) * 1000
        return ScenarioResult(
            scenario_id="BASELINE",
            status=ResultStatus.ERROR,
            expected_behavior=f"HTTP {config.health_check.expected_status} from {url}",
            observed_behavior=f"Health request failed: {exc}",
            evidence=[Evidence(name="url", value=url)],
            reproduction_steps=[f"GET {url}"],
            duration_ms=duration_ms,
        )

    duration_ms = (perf_counter() - started) * 1000
    passed = response.status_code == config.health_check.expected_status
    return ScenarioResult(
        scenario_id="BASELINE",
        status=ResultStatus.PASSED if passed else ResultStatus.FAILED,
        expected_behavior=f"HTTP {config.health_check.expected_status} from {url}",
        observed_behavior=f"HTTP {response.status_code}: {response.text}",
        evidence=[
            Evidence(name="url", value=url),
            Evidence(name="status_code", value=response.status_code),
            Evidence(name="response_body", value=response.text),
        ],
        reproduction_steps=[f"GET {url}"],
        duration_ms=duration_ms,
    )
