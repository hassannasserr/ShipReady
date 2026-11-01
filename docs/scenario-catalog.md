# Scenario Catalog

ShipReady currently supports six scenarios against the controlled Demo
Commerce application.

| ID | Scenario | Verification |
|---|---|---|
| I-01 | Database unavailable | Stops the approved `mongo` service, observes a database-dependent failure, restores it, and verifies the order remains readable. |
| I-02 | Dependency latency | Applies a bounded 2000 ms delay to non-health requests, measures the request, removes the delay, and verifies recovery. |
| I-03 | Application restart | Restarts only `app`, waits for health, and verifies persistent order state. |
| B-01 | Duplicate request/idempotency | Repeats a payment with one idempotency key and checks for one logical payment. |
| B-02 | Invalid state transition | Attempts payment after cancellation and checks the response and unchanged state. |
| B-03 | Business invariants | Evaluates only the configured payment/order invariants and returns `not_verified` when evidence is insufficient. |

Every result includes expected behavior, observed behavior, evidence, and
reproduction steps. `passed` means the configured behavior was verified;
`failed` means evidence demonstrates a violation; `error` means ShipReady
could not execute reliably; and `not_verified` means evidence was insufficient.

The corrected implementation is expected to pass all six scenarios. The
`duplicate-payment` fixture should trigger B-01, and `invalid-transition`
should trigger B-02. Infrastructure scenarios are intentionally controlled by
the local Compose environment and are not production tests.
