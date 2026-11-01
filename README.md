# ShipReady — Technical Specification & Implementation Guide

> **Tagline:** Break it before users do.  
> **Project type:** Local QA automation and production-readiness assessment tool  
> **Status:** MVP — implementation in progress (Phase 0 complete)
> **Primary goal:** Detect and report infrastructure failures and business-logic defects using controlled fault injection, explicit expected behavior, and verifiable evidence.

---

## 1. Project Overview

ShipReady is a local-first QA engineering tool that evaluates how an application behaves under selected failure scenarios before deployment.

Traditional happy-path testing verifies that an application works when everything goes as expected. ShipReady focuses on what happens when dependencies fail, requests are repeated, processes restart, or business operations encounter unexpected conditions.

ShipReady should:

1. Accept a GitHub repository and a specific commit or branch.
2. Inspect the project and determine whether it is compatible with the current MVP.
3. Prepare an isolated test environment.
4. Run baseline checks before introducing failures.
5. Execute infrastructure and business-logic failure scenarios.
6. Verify the application's behavior using explicit expectations and business invariants.
7. Collect evidence and produce a structured report.
8. Clean up the test environment safely.

**Important limitation:** ShipReady does not guarantee that an application is production-ready or defect-free. It reports what was tested, what failed, what passed, and what remains unverified.

## 2. Instructions for the Coding Agent

Implement the actual working application described in this document. Do not stop after creating an architecture, generating placeholder files, or writing documentation.

Follow these implementation rules:

- Implement the project incrementally, starting with the smallest working end-to-end flow.
- Use Python for the ShipReady agent and testing engine.
- Use Node.js, Express, and MongoDB for the controlled demo application.
- Use Docker Compose to orchestrate the demo environment.
- Use pytest for automated tests and HTTPX for HTTP requests.
- Use SQLite for local run metadata and result storage.
- Generate JSON and HTML reports.
- Write type hints, docstrings for public interfaces, and useful error messages.
- Add unit tests and integration tests for every important component.
- Use real implementations rather than empty functions, fake success responses, or TODO-only modules.
- Do not claim a feature is implemented until its tests pass.
- If a capability cannot be safely or reliably implemented, document the limitation instead of simulating success.
- Keep the application runnable locally without requiring a cloud account or paid service.
- Do not introduce a frontend framework during the initial MVP.
- Update the README whenever commands, configuration, architecture, or behavior change.

If a decision is not specified, choose the simplest secure option that preserves the requirements below. Document the decision.

## 3. Core Requirements

### 3.1 Repository integration

ShipReady must support a GitHub repository URL.

The initial implementation should:

- Accept a repository URL through the CLI.
- Clone the repository into a ShipReady-managed workspace.
- Support selecting a branch or commit.
- Record the resolved commit SHA in every run.
- Prefer a specific commit SHA for reproducible runs.
- Detect whether the repository matches a supported project configuration.
- Never modify or push changes to the original repository.
- Never automatically install or execute arbitrary scripts simply because they exist in the repository.

The Git operation must be separated from application execution. Repository access should use the user's existing Git credential configuration where applicable. ShipReady must not request or persist GitHub passwords or personal access tokens in its own database.

For the first version, prioritize public repositories and explicitly configured projects. Private repository access may use existing local Git authentication if available.

### 3.2 Local execution

The ShipReady agent runs on the developer's machine.

The target application and its dependencies run in a controlled Docker Compose environment. The agent orchestrates the run from outside the application containers.

The target application must not receive access to:

- The host's filesystem beyond explicitly approved test artifacts.
- The Docker socket.
- Host credentials or ShipReady's internal database.
- Production databases or services.
- Unrestricted host networking.

The MVP must not execute failure scenarios against a live production environment.

### 3.3 Testing scope

The initial MVP must include:

**Infrastructure scenarios**

- I-01: Database unavailable.
- I-02: Controlled dependency latency or timeout.
- I-03: Application process restart.

**Business-logic scenarios**

- B-01: Duplicate request and idempotency.
- B-02: Invalid business-state transition.
- B-03: Business invariant violation and data-integrity verification.

Every scenario must define its preconditions, expected behavior, verification method, cleanup behavior, and result classification.

### 3.4 Evidence-based reporting

A report must distinguish between:

- A confirmed scenario pass.
- A confirmed behavioral failure.
- An execution error.
- A scenario that could not be verified.
- A scenario that was intentionally skipped.

A successful HTTP status code alone is not sufficient evidence that a business operation succeeded correctly.

---

## 4. Technology Stack

| Component | Technology |
|---|---|
| Local agent | Python 3.11+ |
| CLI | Typer |
| Test framework | pytest |
| HTTP client | HTTPX |
| Validation and configuration models | Pydantic |
| Local result storage | SQLite |
| Repository operations | Git CLI |
| Test environment | Docker Engine and Docker Compose |
| Demo application | Node.js + Express |
| Demo database | MongoDB |
| Report output | JSON + self-contained HTML |
| Python packaging | pyproject.toml |

Use compatible, stable dependency versions and pin or constrain dependencies in `pyproject.toml`. Document the versions used during development.

The MVP does not require React, Angular, Kubernetes, a remote API server, or a hosted database.

---

## 5. System Architecture

The implementation should use the following logical components:

### 5.1 CLI

Responsible for:

- Parsing user commands and options.
- Validating input.
- Starting a run.
- Displaying progress and the report location.
- Returning meaningful exit codes.

The CLI must not contain scenario-specific testing logic.

### 5.2 GitHub Adapter

Responsible for:

- Validating repository URLs.
- Cloning repositories into a controlled workspace.
- Checking out a requested branch or commit.
- Recording the resolved commit SHA.
- Handling Git errors without exposing credentials in logs.

Do not construct shell commands by concatenating user-supplied strings. Prefer subprocess argument lists, controlled working directories, and explicit timeouts.

### 5.3 Project Detector and App Adapter

Responsible for identifying a supported project and defining how to launch and verify it.

The MVP should support the included Demo Commerce API first. External repositories must provide a reviewed ShipReady configuration defining their startup method, health endpoint, test database, and allowed scenarios.

Do not automatically execute arbitrary repository-provided startup commands, Dockerfiles, package scripts, or Compose files without explicit review and approval.

### 5.4 Safety Controller

Responsible for enforcing execution boundaries.

It must validate:

- The repository and commit selected for testing.
- The approved application configuration.
- The permitted Docker Compose project and services.
- The test database and data isolation.
- Resource and time limits.
- Allowed network communication.
- Cleanup behavior.

If required safety conditions are not satisfied, the run must stop before the target application executes.

### 5.5 Baseline Engine

Responsible for collecting the application's normal behavior before fault injection.

At minimum, it should:

- Start the approved test environment.
- Verify the health endpoint.
- Check that required dependencies are available.
- Execute baseline API checks.
- Record response codes, durations, and relevant data state.
- Determine whether the application is healthy enough to test.

Do not run fault scenarios when the baseline fails. Report that the run was blocked by baseline failure.

### 5.6 Scenario Engine

Responsible for running individual scenarios.

Each scenario must follow this lifecycle:

1. Validate prerequisites.
2. Prepare isolated test data.
3. Record initial state when applicable.
4. Execute the fault or business-logic action.
5. Send the required HTTP requests.
6. Observe the response and system state.
7. Verify expected behavior and invariants.
8. Attempt recovery when relevant.
9. Collect evidence.
10. Clean up and return a `ScenarioResult`.

A scenario must not silently change its expected result to match observed behavior.

### 5.7 Evidence Engine

Responsible for collecting and associating evidence with each result.

Evidence may include:

- HTTP status codes and response bodies.
- Request identifiers and idempotency keys.
- Before-and-after business state.
- Relevant application logs.
- Service health observations.
- Timing information.
- Recovery verification results.
- The scenario configuration and run identifier.

Redact credentials, authorization headers, secrets, and sensitive environment values. Limit log size and avoid collecting unrelated files or environment variables.

### 5.8 Reporter

Responsible for generating:

- A machine-readable JSON report.
- A readable standalone HTML report.
- A concise terminal summary.

Reports must be generated even when a scenario fails, provided the report system itself remains operational.

### 5.9 Storage

Use SQLite for run metadata and structured scenario results.

Store large logs and evidence files in the run's artifact directory. The database should reference those files instead of storing unlimited log content directly.

---

## 6. Required Repository Structure

Create the following project structure. Additional files may be added where necessary, but preserve these responsibilities.

```text
shipready/
├── agent/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   └── run_manager.py
│
├── adapters/
│   ├── __init__.py
│   ├── github_adapter.py
│   ├── project_detector.py
│   └── app_adapter.py
│
├── safety/
│   ├── __init__.py
│   ├── policy.py
│   ├── sandbox.py
│   └── cleanup.py
│
├── engines/
│   ├── __init__.py
│   ├── baseline/
│   │   ├── __init__.py
│   │   └── runner.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database_outage.py
│   │   ├── dependency_latency.py
│   │   └── process_restart.py
│   └── business/
│       ├── __init__.py
│       ├── duplicate_request.py
│       ├── invalid_transition.py
│       └── invariants.py
│
├── evidence/
│   ├── __init__.py
│   ├── collector.py
│   └── models.py
│
├── reporting/
│   ├── __init__.py
│   ├── json_report.py
│   └── html_report.py
│
├── storage/
│   ├── __init__.py
│   ├── database.py
│   └── repositories.py
│
├── demo_app/
│   ├── package.json
│   ├── package-lock.json
│   ├── Dockerfile
│   ├── src/
│   │   ├── app.js
│   │   ├── server.js
│   │   ├── routes/
│   │   │   ├── health.routes.js
│   │   │   └── orders.routes.js
│   │   ├── services/
│   │   │   └── payment.service.js
│   │   ├── models/
│   │   │   ├── order.model.js
│   │   │   └── payment.model.js
│   │   └── middleware/
│   │       └── error-handler.js
│   └── tests/
│       └── ...
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── safety/
│   └── scenarios/
│
├── configs/
│   └── demo-project.yaml
│
├── docker/
│   └── compose.yaml
│
├── docs/
│   ├── architecture.md
│   ├── scenario-catalog.md
│   └── security-model.md
│
├── artifacts/
│   └── .gitkeep
│
├── pyproject.toml
├── .gitignore
├── .dockerignore
├── README.md
├── SECURITY.md
└── LICENSE
```

### Directory responsibilities

- `agent/`: CLI entry point, application configuration, and run orchestration.
- `adapters/`: Git operations and application-specific integration.
- `safety/`: execution policies, sandbox management, and cleanup.
- `engines/baseline/`: normal behavior checks.
- `engines/infrastructure/`: controlled dependency and process failures.
- `engines/business/`: business scenarios and invariant verification.
- `evidence/`: evidence models and collection.
- `reporting/`: JSON and HTML report generation.
- `storage/`: SQLite initialization and persistence operations.
- `demo_app/`: a deliberately controlled application for validating ShipReady.
- `tests/`: automated tests for ShipReady itself.
- `configs/`: reviewed project configuration examples.
- `docker/`: approved Compose configuration for the demo environment.
- `docs/`: detailed technical and security documentation.
- `artifacts/`: local reports and evidence; generated files must not be committed by default.

---

## 7. Core Data Models

Implement shared models using Pydantic or dataclasses with explicit validation. Use one consistent schema across all engines.

### 7.1 ScenarioResult

Every scenario must return a result with the following fields:

```python
from dataclasses import dataclass, field
from typing import Literal

ScenarioStatus = Literal[
    "passed",
    "failed",
    "error",
    "not_verified",
    "skipped",
]

@dataclass
class ScenarioResult:
    scenario_id: str
    category: str
    status: ScenarioStatus
    severity: str
    summary: str
    started_at: str
    duration_ms: int
    evidence: list[dict] = field(default_factory=list)
    reproduction_steps: list[str] = field(default_factory=list)
    recovery_verified: bool | None = None
    error_message: str | None = None
```

Validate all externally supplied values before use. Timestamps should use ISO 8601 format.

Status meanings:

- `passed`: the specified behavior was verified.
- `failed`: sufficient evidence demonstrates a violation.
- `error`: the testing tool could not execute or complete the scenario reliably.
- `not_verified`: the available evidence is insufficient to determine the outcome.
- `skipped`: the scenario was intentionally not executed.

A scenario that crashes due to an infrastructure problem in ShipReady must not automatically be marked as a product defect.

### 7.2 Run metadata

Each run must record:

- Unique run ID.
- Repository URL.
- Resolved commit SHA.
- Branch when applicable.
- Start and end timestamps.
- ShipReady version.
- Project configuration.
- Baseline status.
- Scenario results.
- Overall summary.
- Artifact directory.
- Cleanup status.

### 7.3 Severity

Use these levels:

- `critical`: a demonstrated high-impact integrity or security failure.
- `high`: a major business workflow or availability failure.
- `medium`: a meaningful defect with limited or recoverable impact.
- `low`: a minor issue.
- `info`: an observation without a demonstrated defect.

Severity must be grounded in evidence and configured business impact. Do not assign `critical` merely because a test failed.

---

## 8. Scenario Specifications

Every scenario must have a documented contract and automated tests.

### I-01: Database Unavailable

**Purpose:** Verify behavior when the application's database becomes unavailable.

**Preconditions:**

- The application and disposable test database are running.
- Baseline health checks pass.
- Initial state can be captured.
- The database service is controlled by the approved test environment.

**Execution:**

1. Capture the initial business state.
2. Disable the application's database connectivity using a controlled mechanism.
3. Send a request requiring database access.
4. Observe the response and application logs.
5. Restore connectivity.
6. Verify service recovery.
7. Check data integrity and clean up.

**Expected behavior:**

- The application must not falsely report a successful database-dependent operation.
- It must handle the failure according to its documented contract.
- After recovery, data must remain consistent with the operation's actual outcome.

Do not require a specific HTTP status code unless the project configuration defines one.

### I-02: Dependency Latency or Timeout

**Purpose:** Verify that delayed dependencies do not cause uncontrolled hanging or unsafe retries.

**Execution:**

1. Confirm baseline health.
2. Add a controlled delay to an approved test dependency.
3. Send a request that uses the dependency.
4. Measure response time and outcome.
5. Verify the configured timeout or fallback behavior.
6. Remove the delay and verify recovery.

**Expected behavior:**

- Requests respect the configured timeout budget.
- The tool distinguishes an application timeout from its own test timeout.
- Retry behavior does not duplicate a non-idempotent business operation.
- Recovery is verified after the fault is removed.

If the target application's timeout contract is unknown, report `not_verified` rather than inventing one.

### I-03: Application Process Restart

**Purpose:** Verify recovery after a controlled application restart.

**Execution:**

1. Start a test workflow and capture its state.
2. Restart the approved application service.
3. Wait for the health check to recover, subject to a fixed timeout.
4. Re-check the workflow and persisted state.
5. Verify that completed operations remain correct and incomplete operations are handled consistently.

Never restart arbitrary host processes or production services.

### B-01: Duplicate Request and Idempotency

**Purpose:** Detect duplicate business effects caused by repeated requests.

**Demo API:** `POST /orders/{order_id}/pay`

The demo API must support an `Idempotency-Key` for payment requests.

**Execution:**

1. Create a test order.
2. Record the initial order and payment state.
3. Submit a payment request with a unique idempotency key.
4. Repeat the same request with the same key.
5. Compare the payment records and business state.

**Expected behavior:**

- One logical payment operation is recorded.
- Repeated requests follow the documented idempotency contract.
- The same request must not cause duplicate financial effects.
- The final order state must be consistent with the recorded payment.

A repeated request may return the original result or an appropriate conflict response, depending on the contract.

### B-02: Invalid Business-State Transition

**Purpose:** Verify that an operation cannot move an entity into an invalid state.

Use the demo order workflow:

`pending → paid → completed`

A cancelled order must not be paid, and a completed order must not transition back to pending unless the project explicitly supports that behavior.

**Execution:**

1. Create an order in a known state.
2. Attempt an invalid transition.
3. Verify the response.
4. Verify that the entity state and related records remain unchanged.

The expected state transitions must be explicit and testable.

### B-03: Business Invariant Violation

**Purpose:** Verify data integrity across a business operation.

For the demo payment workflow, define invariants such as:

- A payment has a unique logical operation identifier.
- A successful payment is associated with the correct order.
- A repeated idempotent request does not create a second logical payment.
- The order's paid state is consistent with its payment record.
- A failed payment must not be represented as successful.

Use deterministic test data and compare state before and after the operation.

Do not claim to detect arbitrary business-rule violations automatically. The MVP verifies configured invariants and scenarios.

---

## 9. Demo Application Requirements

The Demo Commerce API is required to validate the entire product.

Implement:

- `GET /health`
- `POST /orders`
- `GET /orders/{order_id}`
- `POST /orders/{order_id}/pay`
- `POST /orders/{order_id}/cancel`

Use MongoDB for persistence.

The demo application must:

1. Use synthetic data only.
2. Implement a clear order-state model.
3. Implement payment idempotency.
4. Expose deterministic behavior for testing.
5. Include a controlled mechanism to reproduce selected defects in a test-only build or test fixture.
6. Never enable intentional faults in a normal application run.
7. Include API tests independent of the ShipReady engine.

Create at least one intentionally defective implementation for each major business scenario, or provide deterministic test fixtures that simulate the defect. Then prove that ShipReady detects the defect and passes the corrected implementation.

Do not build an actual banking or payment integration. All payments must be simulated.

---

## 10. Configuration

Use a validated YAML configuration file.

Initial example:

```yaml
project:
  name: demo-commerce
  adapter: demo-express
  base_url: http://app:3000

health_check:
  path: /health
  expected_status: 200
  timeout_seconds: 5

database:
  type: mongodb
  disposable_test_database: true

execution:
  max_run_seconds: 300
  scenario_timeout_seconds: 30
  allow_external_network: false

scenarios:
  - I-01
  - B-01
  - B-02
  - B-03
```

This is a schema example, not permission to trust arbitrary values.

The configuration loader must validate URLs, timeouts, supported scenario IDs, and the permitted execution environment.

For the MVP:

- Only approved internal application URLs may be targeted.
- Only disposable test databases may be used.
- Arbitrary hostnames and production-looking URLs must not be accepted by default.
- Repository-provided configuration must be reviewed before execution.
- Unsupported configuration must produce a clear error.

The configuration must not contain credentials or secrets.

---

## 11. Safety and Isolation Requirements

Safety is a core feature, not an optional enhancement.

### 11.1 Untrusted repository handling

Treat repository content as untrusted.

- Validate the repository URL.
- Use a managed workspace.
- Set timeouts for Git operations.
- Do not execute repository scripts during inspection.
- Do not install dependencies automatically from an arbitrary repository without explicit approval.
- Review Dockerfiles and Compose definitions before running them.
- Do not use repository-controlled privileged containers or host mounts.
- Do not expose the host Docker socket to the target application.

### 11.2 Container restrictions

The target application must run with the minimum required privileges.

Where supported:

- Run as a non-root user.
- Drop unnecessary Linux capabilities.
- Use `no-new-privileges`.
- Apply CPU, memory, process, and execution-time limits.
- Use read-only filesystems where practical.
- Use a disposable data volume.
- Keep application and database services on an isolated network.
- Disable external network egress by default.

Docker is not a complete security boundary against malicious code. For untrusted repositories, recommend a dedicated VM or equivalent stronger isolation. Never describe the MVP as safe for arbitrary hostile repositories on a sensitive workstation.

### 11.3 Fault injection restrictions

Fault injection must target only explicitly approved services inside the ShipReady test environment.

- No production testing.
- No host-wide process termination.
- No arbitrary container deletion.
- No uncontrolled resource exhaustion.
- No unbounded latency.
- No network attack against external services.
- No destructive operations outside the disposable test environment.

### 11.4 Cleanup

Cleanup must run after success, failure, timeout, and interruption where possible.

It should:

- Remove only resources created by the current ShipReady run.
- Use unique Compose project identifiers.
- Preserve reports and required evidence.
- Record cleanup success or failure.
- Avoid deleting user-owned Docker resources.
- Never run broad destructive commands.

If cleanup fails, the report must prominently identify the remaining resources and provide safe manual cleanup instructions.

---

## 12. CLI Requirements

Implement a CLI named `shipready`.

The following interface is the target contract:

```bash
shipready --help

shipready doctor

shipready inspect \
  --repo https://github.com/OWNER/REPOSITORY \
  --ref COMMIT_OR_BRANCH

shipready run \
  --repo https://github.com/OWNER/REPOSITORY \
  --ref COMMIT_SHA \
  --config configs/demo-project.yaml

shipready report \
  --run-id RUN_ID

shipready list-runs
```

Expected behavior:

- `doctor`: check Python dependencies, Git, Docker, and Docker Compose availability.
- `inspect`: clone or update the repository and perform non-executing compatibility checks.
- `run`: validate safety, prepare the environment, run baseline checks, execute enabled scenarios, collect evidence, generate reports, and clean up.
- `report`: locate and display an existing run's report.
- `list-runs`: list locally stored runs.

The commands are a proposed interface. Implement them consistently and document any justified changes.

The run command must require explicit configuration and confirmation before executing target code. Inspection must never launch the target application.

Use clear exit codes. A suggested mapping is:

- `0`: execution completed without confirmed scenario failures.
- `1`: one or more scenarios failed.
- `2`: invalid input or configuration.
- `3`: safety validation blocked execution.
- `4`: infrastructure or execution error prevented a reliable assessment.

If a run contains only `not_verified` or `skipped` scenarios, it must not be presented as a clean pass. Document the precise exit-code policy and apply it consistently.

---

## 13. Report Format

Generate one JSON report and one standalone HTML report per run.

Suggested JSON structure:

```json
{
  "schema_version": "1.0",
  "run_id": "example-run-id",
  "project": {
    "name": "demo-commerce",
    "repository": "https://github.com/OWNER/REPOSITORY",
    "commit_sha": "resolved-commit-sha"
  },
  "summary": {
    "total": 6,
    "passed": 4,
    "failed": 1,
    "errors": 0,
    "not_verified": 1,
    "skipped": 0
  },
  "scenarios": [
    {
      "scenario_id": "B-01",
      "category": "business",
      "status": "failed",
      "severity": "high",
      "summary": "Repeated payment request created duplicate logical payment records.",
      "evidence": [],
      "reproduction_steps": [],
      "recovery_verified": null
    }
  ],
  "cleanup": {
    "status": "succeeded"
  }
}
```

The example is illustrative. The generated report must contain real data from the current run.

The HTML report must show:

- Repository and commit SHA.
- Run timestamp and duration.
- Baseline outcome.
- Scenario totals by status.
- Each scenario's category and severity.
- Expected versus observed behavior.
- Evidence references.
- Reproduction steps.
- Recovery outcome.
- Unverified and skipped scenarios.
- Safety or cleanup warnings.

Escape untrusted strings before rendering them into HTML. Do not execute HTML, JavaScript, or other active content from collected logs or repository metadata.

The report must clearly state that its findings apply only to the tested commit, configuration, scenarios, and environment.

---

## 14. Storage Design

Use SQLite to persist run metadata and scenario summaries.

At minimum, implement tables for:

### `runs`

- `id`
- `repository_url`
- `commit_sha`
- `branch`
- `project_name`
- `started_at`
- `finished_at`
- `baseline_status`
- `overall_status`
- `report_path`
- `artifact_path`
- `cleanup_status`

### `scenario_results`

- `id`
- `run_id`
- `scenario_id`
- `category`
- `status`
- `severity`
- `summary`
- `duration_ms`
- `recovery_verified`
- `evidence_json`
- `reproduction_steps_json`
- `error_message`

Use foreign keys and transactions where appropriate. Create a database migration or schema initialization strategy and test it.

Keep generated reports and logs outside the source tree or inside an ignored artifact directory.

---

## 15. Testing Strategy

ShipReady must test itself.

### Unit tests

Cover:

- Configuration validation.
- Scenario result validation.
- Severity and status mapping.
- Report serialization.
- SQLite persistence.
- URL validation.
- Safety policy checks.
- Exit-code calculation.

### Integration tests

Cover:

- Git clone and commit resolution.
- Docker Compose startup and teardown.
- Health checks.
- Database connectivity.
- Evidence collection.
- Report generation.
- Cleanup after an intentional test failure.

### Scenario tests

For each scenario:

1. Run against the corrected demo implementation.
2. Verify the expected pass behavior.
3. Run against a controlled defective implementation.
4. Verify that the expected defect is detected.
5. Confirm that the report includes sufficient evidence.
6. Verify that the environment is cleaned up.

### Safety tests

Verify that ShipReady refuses to execute when:

- The repository configuration is missing or invalid.
- A production target is specified.
- An unapproved external URL is used.
- Required isolation controls are unavailable.
- A scenario attempts to target a service outside the approved environment.
- Execution exceeds its configured timeout.
- Cleanup is requested for resources not owned by the current run.

Never use a real production system for these tests.

---

## 16. Implementation Roadmap

Implement the project in the following order.

### Phase 1 — Foundation

1. Create `pyproject.toml` and the Python package.
2. Implement the CLI and `doctor` command.
3. Implement configuration loading and validation.
4. Build the Demo Commerce API.
5. Create the approved Docker Compose environment.
6. Implement SQLite schema initialization.
7. Implement baseline health checks.
8. Generate the first JSON report.
9. Add unit and integration tests.

**Acceptance criteria:** ShipReady can run a baseline assessment against the demo application and persist a real report.

### Phase 2 — Business Logic

1. Implement the shared scenario interface.
2. Implement B-01 duplicate request.
3. Implement B-02 invalid state transition.
4. Implement B-03 invariant verification.
5. Implement before-and-after state capture.
6. Add evidence collection.
7. Test both corrected and intentionally defective demo implementations.

**Acceptance criteria:** ShipReady detects the seeded business-logic defects and does not report a pass when the invariant is violated.

### Phase 3 — Infrastructure Failures

1. Implement controlled database unavailability.
2. Implement controlled dependency latency.
3. Implement application process restart.
4. Add recovery verification.
5. Add timeouts and resource limits.
6. Add cleanup for interrupted runs.
7. Test execution failures separately from application failures.

**Acceptance criteria:** Each infrastructure scenario produces an evidence-based result and attempts recovery safely.

### Phase 4 — GitHub Integration and Reports

1. Implement repository cloning and commit selection.
2. Implement non-executing project inspection.
3. Require reviewed configuration before target execution.
4. Add JSON and HTML reports.
5. Add run history and report lookup.
6. Add security documentation and reproducible setup instructions.
7. Run the complete test suite from a clean environment.

**Acceptance criteria:** A developer can select a supported GitHub commit, approve the configuration, execute the MVP locally, and inspect the resulting report.

Do not postpone all testing until the end. Every phase must include tests before moving to the next.

---

## 17. Definition of Done

The MVP is complete only when all the following are true:

- [ ] The Python package installs in a clean environment.
- [ ] `shipready doctor` provides actionable diagnostics.
- [ ] The demo application starts using the documented Docker Compose setup.
- [ ] A baseline assessment can be run from the CLI.
- [ ] The GitHub adapter resolves and records a specific commit SHA.
- [ ] Unsupported or unsafe configurations are rejected before execution.
- [ ] All six defined scenarios have implementations or explicit, tested compatibility limitations.
- [ ] The business-logic scenarios detect their corresponding seeded defects.
- [ ] Infrastructure scenarios verify recovery where applicable.
- [ ] Results distinguish `passed`, `failed`, `error`, `not_verified`, and `skipped`.
- [ ] Evidence is associated with the correct run and scenario.
- [ ] JSON and HTML reports are generated.
- [ ] Results are persisted in SQLite.
- [ ] Cleanup runs after normal completion and is tested for failure paths.
- [ ] No credentials or secrets are stored in reports.
- [ ] Unit, integration, scenario, and safety tests pass.
- [ ] README setup instructions work on a clean machine with the documented prerequisites.
- [ ] Known limitations are documented honestly.

A scenario that cannot be implemented safely must be reported as unsupported or unverified. Do not create a placeholder that always passes.

---

## 18. Local Development Setup

The intended setup flow is:

1. Install Python 3.11 or later.
2. Install Git.
3. Install Docker Engine or Docker Desktop with Docker Compose support.
4. Clone the ShipReady repository.
5. Create a Python virtual environment.
6. Install the project and development dependencies.
7. Run the diagnostic command.
8. Start the demo environment using the documented workflow.
9. Run unit tests.
10. Run the baseline assessment.
11. Inspect the generated reports.

The implementation must provide exact commands for Windows PowerShell and Linux/macOS in the final documentation.

Example Python environment setup:

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
shipready doctor
```

**Linux/macOS**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
shipready doctor
```

Adjust these commands if the final packaging configuration differs. Do not claim Docker or the demo environment is ready until its health checks pass.

### Phase 0 verification

Phase 0 provides the installable Python package, the documented repository
layout, development tooling configuration, and the environment diagnostic
command. From the repository root, run:

```text
shipready --help
shipready doctor
python -m pytest
python -m ruff check .
python -m mypy
```

`shipready doctor` checks Python 3.11+, the installed runtime dependencies,
Git, Docker, and Docker Compose. A missing prerequisite is reported with an
actionable installation hint. Phase 0 does not execute target repositories,
start the demo application, or create Docker resources; those behaviors belong
to later phases.

### Phase 1 demo environment

The controlled Demo Commerce API uses Node.js, Express, and MongoDB. Docker
Compose exposes only the API on `127.0.0.1`; MongoDB is available only on the
internal Compose network and uses a disposable named volume.

From the repository root, start the environment:

**Windows PowerShell**

```powershell
docker compose -f .\docker\compose.yaml up --build -d
docker compose -f .\docker\compose.yaml ps
curl.exe http://127.0.0.1:3000/health
```

**Linux/macOS**

```bash
docker compose -f ./docker/compose.yaml up --build -d
docker compose -f ./docker/compose.yaml ps
curl http://127.0.0.1:3000/health
```

The API is ready only when both services report `healthy`. Stop and remove
only this demo environment with:

```text
docker compose -f docker/compose.yaml down -v
```

To run the independent API tests without Docker, install Node.js 22 or later,
then run `npm install` and `npm test` from `demo_app/`. The tests use an
in-memory MongoDB instance and synthetic data.

The reviewed test-only defect fixtures are selected with `DEFECT_MODE`:
`duplicate-payment` bypasses idempotency lookup, and `invalid-transition`
allows payment after cancellation. Do not enable either mode for a corrected
baseline run. No real payment provider or production database is used.

### Phase 2 baseline run

With the demo Compose environment healthy, run the first ShipReady baseline:

```powershell
.\.venv\Scripts\shipready.exe baseline `
  --config configs\demo-project.yaml `
  --artifacts artifacts\phase2 `
  --database artifacts\phase2\shipready.db
```

The command validates the configuration, creates a unique run directory,
requests the configured health endpoint, stores the run and result in SQLite,
and writes `report.json` inside the run directory. A successful run prints its
run ID and report path. A failed health check returns a non-zero exit code and
is recorded as `blocked`.

Run the configured business scenarios after the baseline:

```powershell
.\.venv\Scripts\shipready.exe business --config configs\demo-project.yaml --artifacts artifacts\phase3 --database artifacts\phase3\shipready.db
```

The `business` command always runs the baseline first. If the baseline does
not pass, it records a blocked run and does not execute B-01, B-02, or B-03.
When the baseline passes, it runs the configured business scenarios:

- `B-01` verifies that a repeated payment idempotency key creates one logical
  payment.
- `B-02` verifies that a cancelled order cannot be paid.
- `B-03` verifies only the payment and order invariants configured for the
  Demo Commerce API.

The `business_invariants` list in `configs/demo-project.yaml` is the explicit
allowlist for B-03. Unsupported invariant names are rejected during
configuration validation.

Each result includes expected behavior, observed behavior, evidence, and
reproduction steps. The test-only defective implementations can be run by
recreating Compose with `DEFECT_MODE=duplicate-payment` or
`DEFECT_MODE=invalid-transition`; the corrected implementation must not enable
either mode.

Run the Phase 2 tests and quality checks with:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy
```

---

## 19. Engineering Principles

Use these principles throughout the implementation:

1. **Evidence over assumptions:** Every finding must be supported by collected observations.
2. **Explicit contracts:** Expected business behavior must be configured or documented.
3. **Safe by default:** Never run target code or inject faults before safety validation.
4. **Reproducibility:** Record the commit, configuration, scenario version, and run metadata.
5. **Separation of concerns:** Keep orchestration, scenarios, evidence, storage, and reporting independent.
6. **Honest outcomes:** A testing tool failure is not automatically an application defect.
7. **Small, testable components:** Each scenario should be independently testable.
8. **No false guarantees:** Passing scenarios does not prove complete production readiness.
9. **Incremental delivery:** Keep the MVP runnable throughout implementation.
10. **Document limitations:** Clearly distinguish implemented features from future work.

## 20. Future Scope — Not Required for the MVP

Potential future features include:

- Support for additional programming languages and frameworks.
- A local web dashboard.
- GitHub Actions integration.
- More failure scenarios.
- Custom user-defined invariants.
- Historical comparison between commits.
- Trend analysis across repeated runs.
- Additional application adapters.
- Stronger isolation using disposable virtual machines.
- Optional AI-assisted analysis of evidence, with human-verifiable findings.

Do not implement these features before the core MVP acceptance criteria are satisfied.

---

## Final Instruction

Start by inspecting the existing workspace. If it is empty, initialize the project using the structure above. If code already exists, inspect it and preserve compatible work.

Then implement **Phase 1 completely**, run its tests, and continue through the remaining phases in order. Keep the application runnable, update documentation, and report the exact commands executed, tests passed, tests failed, implemented features, and remaining limitations.

The final deliverable must be a working, locally executable ShipReady MVP — not just an architecture proposal or a collection of placeholder files.
