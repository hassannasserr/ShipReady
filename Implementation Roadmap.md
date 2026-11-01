## Implementation Roadmap: Phases & Steps

ShipReady must be implemented incrementally. Complete each phase, run its tests, verify its acceptance criteria, and update the documentation before starting the next phase.

**Important rules for the coding agent:**
- Follow the phases in the exact order listed below.
- Do not skip steps or implement all phases in one unverified batch.
- Do not leave placeholder functions or fake successful results.
- Keep the project runnable after every phase.
- If a step fails, fix the problem before proceeding.
- At the end of each phase, summarize implemented features, changed files, commands executed, test results, and remaining limitations.
- Do not claim that a phase is complete unless its acceptance criteria are satisfied.

### Phase 0 — Project Setup and Environment Validation

**Goal:** Establish a clean, reproducible development environment.

Steps:

1. Inspect the existing workspace and preserve any compatible implementation.
2. Create the project structure defined in this README.
3. Create `pyproject.toml` with application and development dependencies.
4. Configure Python packaging, formatting, linting, and type checking.
5. Create `.gitignore` and `.dockerignore`.
6. Verify Python, Git, Docker, and Docker Compose availability.
7. Create a basic `shipready doctor` command.
8. Document the environment setup commands for Windows, Linux, and macOS.

**Acceptance criteria:**

- The package installs in a clean Python virtual environment.
- `shipready --help` works.
- `shipready doctor` identifies missing dependencies and provides actionable messages.
- Basic unit tests run successfully.

### Phase 1 — Demo Application and Test Environment

**Goal:** Build a controlled application that ShipReady can test safely and reproducibly.

Steps:

1. Implement the Demo Commerce API using Node.js and Express.
2. Configure MongoDB for disposable test data.
3. Implement the health, order creation, order retrieval, payment, and cancellation endpoints.
4. Implement the order state model and simulated payment workflow.
5. Define the expected behavior and business invariants for each workflow.
6. Create the approved Docker Compose configuration.
7. Add health checks and startup timeouts.
8. Add automated API tests for normal behavior.
9. Create controlled defective variants or test fixtures for the business bugs ShipReady must detect.
10. Document how to start, inspect, and stop the demo environment.

**Acceptance criteria:**

- The demo API starts reliably.
- MongoDB is accessible only through the intended test environment.
- Baseline API tests pass against the corrected implementation.
- Defective variants reproduce known issues deterministically.
- No real payment service or production database is used.

### Phase 2 — Core Agent, Configuration, and Storage

**Goal:** Build the central orchestration layer and the data models shared by all engines.

Steps:

1. Implement configuration loading and validation.
2. Define the shared `ScenarioResult` and run metadata models.
3. Implement SQLite schema initialization and persistence.
4. Implement run IDs and unique artifact directories.
5. Implement the run manager and lifecycle states.
6. Implement the baseline engine and health checks.
7. Collect baseline HTTP responses, timings, and relevant application state.
8. Implement JSON report generation for baseline results.
9. Add tests for configuration, storage, baseline behavior, and report serialization.

**Acceptance criteria:**

- A baseline run can be executed against the demo application.
- The run is persisted in SQLite.
- The generated JSON report contains real results.
- Invalid configurations are rejected.
- A failed baseline prevents fault injection from starting.

### Phase 3 — Business Logic Testing Engine

**Goal:** Detect business-logic defects using explicit expectations and verifiable invariants.

Implement the scenarios in this order.

#### Step 3.1 — B-01: Duplicate Request and Idempotency

1. Create a test order.
2. Record the initial order and payment state.
3. Send a payment request with an idempotency key.
4. Repeat the request using the same key.
5. Compare the resulting payment records and order state.
6. Report duplicate logical operations or inconsistent outcomes.
7. Test both the corrected and defective implementations.

#### Step 3.2 — B-02: Invalid State Transition

1. Prepare an order in a known state.
2. Attempt a transition that violates the configured state model.
3. Verify the API response.
4. Verify that the order and related records remain consistent.
5. Report any forbidden transition or unexpected mutation.

#### Step 3.3 — B-03: Business Invariant Verification

1. Define the invariants supported by the demo application.
2. Capture the relevant initial state.
3. Execute the selected business operation.
4. Read the resulting state from the test environment.
5. Evaluate every applicable invariant.
6. Attach failed invariant checks to the scenario evidence.
7. Verify that insufficient evidence produces `not_verified`, not `passed`.

**Acceptance criteria:**

- All three scenarios have working implementations.
- Seeded defects are detected.
- Corrected implementations pass their defined checks.
- Reports contain expected behavior, observed behavior, evidence, and reproduction steps.
- The engine does not invent business rules that have not been configured.

### Phase 4 — Infrastructure Failure Testing Engine

**Goal:** Verify application behavior and recovery when infrastructure dependencies fail.

#### Step 4.1 — I-01: Database Unavailable

1. Verify that the baseline is healthy.
2. Capture relevant application state.
3. Disable database connectivity using a controlled test mechanism.
4. Send a request that requires database access.
5. Collect the response and relevant logs.
6. Restore connectivity.
7. Verify recovery and data consistency.
8. Record the result and cleanup outcome.

#### Step 4.2 — I-02: Dependency Latency or Timeout

1. Configure a controlled delay on an approved test dependency.
2. Send a request that uses that dependency.
3. Measure the observed response time.
4. Verify the configured timeout or fallback behavior.
5. Check for unsafe duplicate operations or uncontrolled hanging.
6. Remove the delay and verify recovery.

#### Step 4.3 — I-03: Application Process Restart

1. Prepare a test workflow and record its state.
2. Restart only the approved application container.
3. Wait for the health endpoint to recover within the configured timeout.
4. Re-check the workflow and persistent state.
5. Verify that completed operations remain correct.
6. Record any inconsistent or unverified state.

**Acceptance criteria:**

- All three infrastructure scenarios are implemented.
- Faults are injected only into approved test services.
- Recovery is checked where applicable.
- Application failures are distinguished from ShipReady execution errors.
- Timeouts and cleanup are tested.

### Phase 5 — GitHub Integration and Safety Enforcement

**Goal:** Allow developers to select a supported GitHub repository and test a specific revision without executing arbitrary code unsafely.

Steps:

1. Implement GitHub URL validation.
2. Clone repositories into a ShipReady-managed workspace.
3. Support branch selection and explicit commit selection.
4. Resolve and record the exact commit SHA.
5. Implement non-executing project inspection.
6. Validate the reviewed project configuration.
7. Implement safety policy checks before application execution.
8. Enforce isolated test networking and disposable data.
9. Apply execution timeouts and resource limits.
10. Prevent target containers from accessing host credentials, the Docker socket, or sensitive host files.
11. Require explicit approval before running target code.
12. Implement cleanup that removes only resources created by the current run.
13. Add tests for rejected configurations and unsafe execution attempts.

**Acceptance criteria:**

- Inspection does not execute repository scripts.
- The tested commit SHA is recorded in every run.
- Unsupported repositories are rejected with clear explanations.
- Execution cannot start when mandatory safety checks fail.
- Cleanup does not remove unrelated user resources.
- External repositories are never treated as trusted merely because they are hosted on GitHub.

### Phase 6 — Evidence Collection and HTML Reporting

**Goal:** Turn test execution into an understandable, reproducible report.

Steps:

1. Standardize evidence records across all engines.
2. Capture relevant HTTP requests and responses with secrets redacted.
3. Capture state comparisons, timing, health checks, and recovery observations.
4. Link evidence to the correct run and scenario.
5. Generate the structured JSON report.
6. Generate a standalone HTML report.
7. Display scenario status, category, severity, and expected versus observed behavior.
8. Include reproduction steps and evidence references.
9. Show `error`, `not_verified`, and `skipped` results explicitly.
10. Include cleanup status and safety warnings.
11. Test report rendering with malformed or untrusted input.
12. Verify that report generation does not execute content from repository files or logs.

**Acceptance criteria:**

- Both JSON and HTML reports are generated from actual run results.
- Each finding can be traced to its scenario and evidence.
- Secrets are not exposed in reports.
- Unverified scenarios are never presented as successful.
- Reports clearly state the commit and scenarios covered by the assessment.

### Phase 7 — CLI Completion and Run History

**Goal:** Make the complete workflow usable from the terminal.

Steps:

1. Complete `shipready doctor`.
2. Complete `shipready inspect`.
3. Complete `shipready run`.
4. Complete `shipready report`.
5. Complete `shipready list-runs`.
6. Implement consistent command-line validation and exit codes.
7. Add useful progress messages and actionable errors.
8. Ensure failed scenarios still produce reports whenever possible.
9. Verify that interrupted runs attempt safe cleanup.
10. Document all CLI options and examples.

**Acceptance criteria:**

- The CLI provides the documented commands.
- A user can run the complete supported workflow without manually editing internal Python code.
- Run history can be queried locally.
- Exit codes distinguish failed assessments from invalid configuration, safety blocks, and execution errors.

### Phase 8 — Quality Assurance, Security Review, and Release

**Goal:** Validate the whole product from a clean installation.

Steps:

1. Run all unit tests.
2. Run all integration tests.
3. Run all six scenarios against the corrected demo application.
4. Run the scenarios against the corresponding controlled defective variants.
5. Verify evidence completeness.
6. Test timeout and interrupted-run behavior.
7. Test cleanup after normal completion and failure.
8. Review Docker permissions, networking, mounts, and resource limits.
9. Check that reports and logs do not contain secrets.
10. Run formatting, linting, and type checking.
11. Test installation and usage from a clean environment.
12. Update the README, architecture documentation, scenario catalog, and security documentation.
13. Record known limitations and unsupported configurations.
14. Produce a final implementation summary.

**Acceptance criteria:**

- The documented tests pass, or every remaining failure is explicitly reported.
- The corrected demo application passes the supported scenarios.
- The controlled defective variants trigger the expected findings.
- No safety check is bypassed to make a test pass.
- Setup and usage instructions have been verified.
- The final report accurately describes implemented features and remaining limitations.

---

## Phase Completion Protocol

At the end of every phase, the coding agent must provide:

1. **Implemented:** What now works.
2. **Files changed:** New and modified files.
3. **Commands executed:** The actual commands used.
4. **Test results:** Passed, failed, skipped, and unverified counts.
5. **Acceptance criteria:** Which criteria are satisfied and which are not.
6. **Known limitations:** Issues that remain unresolved.
7. **Next phase:** The next planned implementation steps.

Do not mark a phase complete if its acceptance criteria have not been met.

## Recommended Execution Order

```text
Phase 0: Setup
    ↓
Phase 1: Demo Application
    ↓
Phase 2: Core Agent and Baseline
    ↓
Phase 3: Business Logic Engine
    ↓
Phase 4: Infrastructure Engine
    ↓
Phase 5: GitHub Integration and Safety
    ↓
Phase 6: Evidence and Reports
    ↓
Phase 7: CLI Completion
    ↓
Phase 8: Final QA and Release
```

The agent may create shared interfaces earlier when required by dependencies, but it must still validate each phase independently and preserve the acceptance criteria.

**Final rule:** A working, tested, and documented smaller implementation is better than a large implementation with unverified features. Prioritize correctness, safety, reproducibility, and evidence over the number of features.
