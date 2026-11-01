"""I-01 database unavailable scenario."""

from __future__ import annotations

from time import perf_counter

import httpx

from shipready.engines.business.client import DemoApiClient, response_json
from shipready.engines.infrastructure.common import error_result, wait_for_health
from shipready.engines.infrastructure.controller import ComposeController
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def run_database_outage(
    client: DemoApiClient,
    controller: ComposeController,
    recovery_timeout: float,
) -> ScenarioResult:
    started = perf_counter()
    order = client.create_order()
    order_data = response_json(order)
    if order.status_code != 201 or not order_data or not isinstance(
        order_data.get("id"), str
    ):
        return error_result(
            "I-01",
            "A test order exists before the outage.",
            f"Order creation returned HTTP {order.status_code}.",
            [Evidence(name="create_response", value=order.text)],
            ["POST /orders"],
            started,
        )

    order_id = order_data["id"]
    cleanup_error: str | None = None
    try:
        controller.stop("mongo")
        failed_request = client.get_order(order_id)
        failed = failed_request.status_code >= 500
    except (httpx.HTTPError, OSError, RuntimeError) as exc:
        return error_result(
            "I-01",
            "Database-dependent requests fail while MongoDB is stopped.",
            f"Fault injection failed: {exc}",
            [],
            ["Stop approved mongo service", "GET /orders/{order_id}"],
            started,
        )
    finally:
        try:
            controller.start("mongo")
        except (OSError, RuntimeError) as exc:
            cleanup_error = str(exc)

    recovered = wait_for_health(client, recovery_timeout)
    after = client.get_order(order_id) if recovered else None
    passed = failed and recovered and after is not None and after.status_code == 200
    status = (
        ResultStatus.ERROR
        if cleanup_error
        else ResultStatus.PASSED
        if passed
        else ResultStatus.FAILED
    )
    return ScenarioResult(
        scenario_id="I-01",
        status=status,
        expected_behavior="Database requests fail during outage and recover afterward.",
        observed_behavior=(
            f"During outage HTTP {failed_request.status_code}; "
            f"recovered={recovered}; "
            f"after_status={after.status_code if after else None}."
        ),
        evidence=[
            Evidence(name="outage_response", value=failed_request.text),
            Evidence(name="recovery_health", value=recovered),
            Evidence(
                name="post_recovery_order",
                value=response_json(after) if after else None,
            ),
            Evidence(name="cleanup_error", value=cleanup_error),
        ],
        reproduction_steps=[
            "POST /orders",
            "Stop approved mongo service",
            "GET /orders/{order_id}",
            "Start mongo and wait for health",
            "GET /orders/{order_id}",
        ],
        duration_ms=(perf_counter() - started) * 1000,
    )
