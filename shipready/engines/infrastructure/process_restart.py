"""I-03 application process restart scenario."""

from __future__ import annotations

from time import perf_counter

import httpx

from shipready.engines.business.client import DemoApiClient, response_json
from shipready.engines.infrastructure.common import error_result, wait_for_health
from shipready.engines.infrastructure.controller import ComposeController
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def run_process_restart(
    client: DemoApiClient,
    controller: ComposeController,
    recovery_timeout: float,
) -> ScenarioResult:
    started = perf_counter()
    if not wait_for_health(client, recovery_timeout):
        return error_result(
            "I-03",
            "The application is healthy before restart.",
            "The application did not become healthy before the scenario.",
            [],
            ["Wait for /health", "POST /orders"],
            started,
        )
    try:
        order = client.create_order()
    except httpx.HTTPError as exc:
        return error_result(
            "I-03",
            "A persistent order exists before restart.",
            f"Order creation failed: {exc}",
            [],
            ["Wait for /health", "POST /orders"],
            started,
        )
    order_data = response_json(order)
    if order.status_code != 201 or not order_data or not isinstance(
        order_data.get("id"), str
    ):
        return ScenarioResult(
            scenario_id="I-03",
            status=ResultStatus.NOT_VERIFIED,
            expected_behavior="A persistent order exists before restart.",
            observed_behavior=f"Order creation returned HTTP {order.status_code}.",
            evidence=[Evidence(name="create_response", value=order.text)],
            reproduction_steps=["POST /orders"],
            duration_ms=(perf_counter() - started) * 1000,
        )

    order_id = order_data["id"]
    try:
        controller.restart("app")
    except (OSError, RuntimeError) as exc:
        return ScenarioResult(
            scenario_id="I-03",
            status=ResultStatus.ERROR,
            expected_behavior="Only the approved app service is restarted.",
            observed_behavior=f"Restart failed: {exc}",
            evidence=[],
            reproduction_steps=["POST /orders", "Restart approved app service"],
            duration_ms=(perf_counter() - started) * 1000,
        )

    recovered = wait_for_health(client, recovery_timeout)
    after = client.get_order(order_id) if recovered else None
    passed = recovered and after is not None and after.status_code == 200
    return ScenarioResult(
        scenario_id="I-03",
        status=ResultStatus.PASSED if passed else ResultStatus.FAILED,
        expected_behavior=(
            "Application recovers and persistent order state remains readable."
        ),
        observed_behavior=(
            f"recovered={recovered}; "
            f"after_status={after.status_code if after else None}."
        ),
        evidence=[
            Evidence(name="recovery_health", value=recovered),
            Evidence(
                name="post_restart_order",
                value=response_json(after) if after else None,
            ),
        ],
        reproduction_steps=[
            "POST /orders",
            "Restart approved app service",
            "Wait for /health",
            "GET /orders/{order_id}",
        ],
        duration_ms=(perf_counter() - started) * 1000,
    )
