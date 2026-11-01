"""B-02 invalid state transition scenario."""

from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from shipready.engines.business.client import DemoApiClient, response_json
from shipready.evidence.models import Evidence, ResultStatus, ScenarioResult


def run_invalid_transition(client: DemoApiClient) -> ScenarioResult:
    """Verify that a cancelled order cannot be paid."""
    started = perf_counter()
    create = client.create_order()
    created = response_json(create)
    if (
        create.status_code != 201
        or not created
        or not isinstance(created.get("id"), str)
    ):
        return ScenarioResult(
            scenario_id="B-02",
            status=ResultStatus.NOT_VERIFIED,
            expected_behavior="A test order can be created before cancellation.",
            observed_behavior=f"Order creation returned HTTP {create.status_code}.",
            evidence=[Evidence(name="create_response", value=create.text)],
            reproduction_steps=["POST /orders"],
            duration_ms=(perf_counter() - started) * 1000,
        )

    order_id = created["id"]
    cancel = client.cancel(order_id)
    payment = client.pay(order_id, f"shipready-{uuid4()}")
    final_response = client.get_order(order_id)
    final = response_json(final_response)
    final_state = final.get("state") if final else None
    final_payments = final.get("payments") if final else None
    passed = (
        cancel.status_code == 200
        and payment.status_code == 409
        and final_response.status_code == 200
        and bool(final)
        and final_state == "cancelled"
        and final_payments == []
    )
    return ScenarioResult(
        scenario_id="B-02",
        status=ResultStatus.PASSED if passed else ResultStatus.FAILED,
        expected_behavior="Cancelled orders reject payment and remain unchanged.",
        observed_behavior=(
            f"Cancel HTTP {cancel.status_code}, payment HTTP {payment.status_code}, "
            f"final_state={final.get('state') if final else None}."
        ),
        evidence=[
            Evidence(
                name="cancel_response",
                value=response_json(cancel) or cancel.text,
            ),
            Evidence(
                name="payment_response",
                value=response_json(payment) or payment.text,
            ),
            Evidence(name="final_order", value=final),
        ],
        reproduction_steps=[
            "POST /orders",
            "POST /orders/{order_id}/cancel",
            "POST /orders/{order_id}/pay",
            "GET /orders/{order_id}",
        ],
        duration_ms=(perf_counter() - started) * 1000,
    )
