"""B-01 duplicate request and idempotency scenario."""

from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from shipready.engines.business.client import DemoApiClient, response_json
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def run_duplicate_request(client: DemoApiClient) -> ScenarioResult:
    """Verify that a repeated payment key creates one logical operation."""
    started = perf_counter()
    create = client.create_order()
    created = response_json(create)
    if (
        create.status_code != 201
        or not created
        or not isinstance(created.get("id"), str)
    ):
        return ScenarioResult(
            scenario_id="B-01",
            status=ResultStatus.NOT_VERIFIED,
            expected_behavior="A test order can be created before payment.",
            observed_behavior=f"Order creation returned HTTP {create.status_code}.",
            evidence=[Evidence(name="create_response", value=create.text)],
            reproduction_steps=["POST /orders"],
            duration_ms=(perf_counter() - started) * 1000,
        )

    order_id = created["id"]
    key = f"shipready-{uuid4()}"
    first = client.pay(order_id, key)
    second = client.pay(order_id, key)
    first_data = response_json(first)
    second_data = response_json(second)
    final = response_json(client.get_order(order_id))
    operation_ids = {
        first_data.get("payment", {}).get("operation_id") if first_data else None,
        second_data.get("payment", {}).get("operation_id") if second_data else None,
    }
    payment_count = len(final.get("payments", [])) if final else None
    passed = (
        first.status_code == 201
        and second.status_code == 200
        and bool(second_data and second_data.get("duplicate") is True)
        and len(operation_ids) == 1
        and None not in operation_ids
        and payment_count == 1
        and final.get("state") == "paid"
        if final
        else False
    )
    return ScenarioResult(
        scenario_id="B-01",
        status=ResultStatus.PASSED if passed else ResultStatus.FAILED,
        expected_behavior="Repeated payment key produces one logical payment.",
        observed_behavior=(
            f"First HTTP {first.status_code}, second HTTP {second.status_code}, "
            f"payments={payment_count}, "
            f"final_state={final.get('state') if final else None}."
        ),
        evidence=[
            Evidence(name="first_response", value=first_data or first.text),
            Evidence(name="second_response", value=second_data or second.text),
            Evidence(name="final_order", value=final),
            Evidence(name="payment_count", value=payment_count),
        ],
        reproduction_steps=[
            "POST /orders",
            "POST /orders/{order_id}/pay with one Idempotency-Key",
            "Repeat the same payment request",
            "GET /orders/{order_id}",
        ],
        duration_ms=(perf_counter() - started) * 1000,
    )
