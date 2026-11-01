"""I-02 controlled dependency latency scenario."""

from __future__ import annotations

from time import perf_counter

import httpx

from shipready.engines.business.client import DemoApiClient
from shipready.engines.infrastructure.common import wait_for_health
from shipready.engines.infrastructure.controller import ComposeController
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def run_dependency_latency(
    client: DemoApiClient,
    controller: ComposeController,
    delay_ms: int,
    recovery_timeout: float,
) -> ScenarioResult:
    started = perf_counter()
    cleanup_error: str | None = None
    try:
        controller.set_delay(delay_ms)
        if not wait_for_health(client, recovery_timeout):
            raise RuntimeError("application did not recover after applying delay")
        delayed_started = perf_counter()
        response = client.create_order()
        elapsed_ms = (perf_counter() - delayed_started) * 1000
    except (httpx.HTTPError, OSError, RuntimeError) as exc:
        return ScenarioResult(
            scenario_id="I-02",
            status=ResultStatus.ERROR,
            expected_behavior=(
                f"Request exceeds the configured {delay_ms}ms delay safely."
            ),
            observed_behavior=f"Fault injection failed: {exc}",
            evidence=[],
            reproduction_steps=["Set approved DEMO_DELAY_MS", "POST /orders"],
            duration_ms=(perf_counter() - started) * 1000,
        )
    finally:
        try:
            controller.set_delay(0)
        except (OSError, RuntimeError) as exc:
            cleanup_error = str(exc)

    recovered = wait_for_health(client, recovery_timeout)
    passed = elapsed_ms >= delay_ms and recovered and response.status_code == 201
    status = (
        ResultStatus.ERROR
        if cleanup_error
        else ResultStatus.PASSED
        if passed
        else ResultStatus.FAILED
    )
    return ScenarioResult(
        scenario_id="I-02",
        status=status,
        expected_behavior=(
            f"Controlled {delay_ms}ms latency is observed and recovery succeeds."
        ),
        observed_behavior=(
            f"HTTP {response.status_code} after {elapsed_ms:.1f}ms; "
            f"recovered={recovered}."
        ),
        evidence=[
            Evidence(name="response_status", value=response.status_code),
            Evidence(name="elapsed_ms", value=elapsed_ms),
            Evidence(name="configured_delay_ms", value=delay_ms),
            Evidence(name="recovery_health", value=recovered),
            Evidence(name="cleanup_error", value=cleanup_error),
        ],
        reproduction_steps=[
            f"Set approved DEMO_DELAY_MS={delay_ms}",
            "POST /orders",
            "Remove delay and verify health",
        ],
        duration_ms=(perf_counter() - started) * 1000,
    )
