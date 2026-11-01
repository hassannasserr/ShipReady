"""B-03 configured business invariant scenario."""

from __future__ import annotations

from collections.abc import Sequence
from time import perf_counter
from uuid import uuid4

from shipready.engines.business.client import DemoApiClient, response_json
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def run_invariants(
    client: DemoApiClient,
    configured_invariants: Sequence[str],
) -> ScenarioResult:
    """Verify configured payment and order consistency invariants."""
    started = perf_counter()
    create = client.create_order()
    created = response_json(create)
    if (
        create.status_code != 201
        or not created
        or not isinstance(created.get("id"), str)
    ):
        return ScenarioResult(
            scenario_id="B-03",
            status=ResultStatus.NOT_VERIFIED,
            expected_behavior="A test order can be created for invariant checks.",
            observed_behavior=f"Order creation returned HTTP {create.status_code}.",
            evidence=[Evidence(name="create_response", value=create.text)],
            reproduction_steps=["POST /orders"],
            duration_ms=(perf_counter() - started) * 1000,
        )

    order_id = created["id"]
    payment_response = client.pay(order_id, f"shipready-{uuid4()}")
    payment_data = response_json(payment_response)
    final_response = client.get_order(order_id)
    final = response_json(final_response)
    payment = payment_data.get("payment") if payment_data else None
    if not configured_invariants:
        status = ResultStatus.NOT_VERIFIED
        invariant_checks: dict[str, bool | None] = {}
    elif not isinstance(payment, dict) or not isinstance(final, dict):
        status = ResultStatus.NOT_VERIFIED
        invariant_checks = {}
    else:
        payments = final.get("payments")
        supported_checks = {
            "payment_has_operation_id": bool(payment.get("operation_id")),
            "payment_is_associated_with_order": (
                payment.get("amount_cents") == final.get("total_cents")
            ),
            "one_logical_payment_recorded": (
                isinstance(payments, list) and len(payments) == 1
            ),
            "paid_order_matches_success": (
                final.get("state") == "paid"
                and payment.get("status") == "succeeded"
            ),
        }
        invariant_checks = {
            invariant: supported_checks[invariant]
            for invariant in configured_invariants
        }
        status = (
            ResultStatus.PASSED
            if all(invariant_checks.values())
            else ResultStatus.FAILED
        )

    return ScenarioResult(
        scenario_id="B-03",
        status=status,
        expected_behavior="Configured payment and order invariants hold.",
        observed_behavior=f"Invariant checks: {invariant_checks}.",
        evidence=[
            Evidence(
                name="payment_response",
                value=payment_data or payment_response.text,
            ),
            Evidence(name="final_order", value=final),
            Evidence(name="invariant_checks", value=invariant_checks),
        ],
        reproduction_steps=[
            "POST /orders",
            "POST /orders/{order_id}/pay",
            "GET /orders/{order_id}",
            "Evaluate configured invariants",
        ],
        duration_ms=(perf_counter() - started) * 1000,
    )
