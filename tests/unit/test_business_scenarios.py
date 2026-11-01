import httpx

from shipready.engines.business.duplicate_request import run_duplicate_request
from shipready.engines.business.invalid_transition import run_invalid_transition
from shipready.engines.business.invariants import run_invariants


def response(status: int, payload: dict) -> httpx.Response:
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", "http://test"),
    )


class CorrectClient:
    def __init__(self) -> None:
        self.pay_calls = 0

    def create_order(self) -> httpx.Response:
        return response(201, {"id": "order-1", "total_cents": 1250})

    def get_order(self, order_id: str) -> httpx.Response:
        return response(
            200,
            {
                "id": order_id,
                "total_cents": 1250,
                "state": "paid",
                "payments": [
                    {
                        "operation_id": "operation-1",
                        "amount_cents": 1250,
                        "status": "succeeded",
                    }
                ],
            },
        )

    def pay(self, order_id: str, key: str) -> httpx.Response:
        self.pay_calls += 1
        return response(
            201 if self.pay_calls == 1 else 200,
            {
                "payment": {
                    "operation_id": "operation-1",
                    "amount_cents": 1250,
                    "status": "succeeded",
                },
                "order": {"state": "paid"},
                "duplicate": self.pay_calls > 1,
            },
        )

    def cancel(self, order_id: str) -> httpx.Response:
        return response(200, {"state": "cancelled"})


class CorrectTransitionClient(CorrectClient):
    def pay(self, order_id: str, key: str) -> httpx.Response:
        return response(409, {"error": "Cannot pay a cancelled order."})

    def get_order(self, order_id: str) -> httpx.Response:
        return response(
            200,
            {"id": order_id, "state": "cancelled", "payments": []},
        )


class DuplicateDefectClient(CorrectClient):
    def pay(self, order_id: str, key: str) -> httpx.Response:
        operation = "operation-1" if key.endswith("first") else "operation-2"
        return response(
            201,
            {
                "payment": {
                    "operation_id": operation,
                    "amount_cents": 1250,
                    "status": "succeeded",
                },
                "order": {"state": "paid"},
                "duplicate": False,
            },
        )

    def get_order(self, order_id: str) -> httpx.Response:
        payload = super().get_order(order_id).json()
        payload["payments"].append(
            payload["payments"][0] | {"operation_id": "operation-2"}
        )
        return response(200, payload)


class InvalidTransitionDefectClient(CorrectClient):
    def pay(self, order_id: str, key: str) -> httpx.Response:
        return response(201, {"order": {"state": "paid"}, "payment": {}})

    def get_order(self, order_id: str) -> httpx.Response:
        return response(
            200,
            {
                "id": order_id,
                "state": "paid",
                "payments": [{"operation_id": "operation-1"}],
            },
        )


class InsufficientEvidenceClient(CorrectClient):
    def pay(self, order_id: str, key: str) -> httpx.Response:
        return response(500, {"error": "payment unavailable"})

    def get_order(self, order_id: str) -> httpx.Response:
        return response(200, {})


def test_correct_business_scenarios_pass() -> None:
    client = CorrectClient()

    assert run_duplicate_request(client).status == "passed"
    assert run_invalid_transition(CorrectTransitionClient()).status == "passed"
    assert (
        run_invariants(
            client,
            [
                "payment_has_operation_id",
                "payment_is_associated_with_order",
                "one_logical_payment_recorded",
                "paid_order_matches_success",
            ],
        ).status
        == "passed"
    )


def test_duplicate_defect_is_detected() -> None:
    assert run_duplicate_request(DuplicateDefectClient()).status == "failed"


def test_invalid_transition_defect_is_detected() -> None:
    assert run_invalid_transition(InvalidTransitionDefectClient()).status == "failed"


def test_insufficient_invariant_evidence_is_not_verified() -> None:
    assert (
        run_invariants(
            InsufficientEvidenceClient(),
            ["payment_has_operation_id"],
        ).status
        == "not_verified"
    )
