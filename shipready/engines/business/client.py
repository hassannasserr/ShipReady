"""HTTP client helpers for the approved Demo Commerce API."""

from __future__ import annotations

from typing import Any

import httpx


class DemoApiClient:
    """Small client restricted to the configured application base URL."""

    def __init__(self, base_url: str, timeout: float) -> None:
        self.client = httpx.Client(base_url=base_url, timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def create_order(self) -> httpx.Response:
        return self.client.post(
            "/orders",
            json={
                "items": [
                    {
                        "sku": "shipready-test-widget",
                        "quantity": 1,
                        "unit_price_cents": 1250,
                    }
                ]
            },
        )

    def get_order(self, order_id: str) -> httpx.Response:
        return self.client.get(f"/orders/{order_id}")

    def pay(self, order_id: str, key: str) -> httpx.Response:
        return self.client.post(
            f"/orders/{order_id}/pay",
            headers={"Idempotency-Key": key},
        )

    def cancel(self, order_id: str) -> httpx.Response:
        return self.client.post(f"/orders/{order_id}/cancel")


def response_json(response: httpx.Response) -> dict[str, Any] | None:
    """Return a JSON object when the response contains one."""
    try:
        value = response.json()
    except ValueError:
        return None
    return value if isinstance(value, dict) else None
