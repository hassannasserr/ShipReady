# Architecture

ShipReady is a local-first assessment tool with a deliberate separation between
inspection, safety policy, scenario execution, evidence, reporting, and storage.

## Flow

1. `shipready inspect` validates a GitHub URL, clones with `--no-checkout`,
   resolves the requested revision, and statically inspects reviewed YAML and
   Compose files. It does not import or execute repository code.
2. `shipready baseline`, `business`, and `infrastructure` load a reviewed local
   configuration and create a unique run in SQLite.
3. The baseline gate runs before business or infrastructure fault injection.
4. Scenario engines use the approved Demo Commerce HTTP client and, for Phase 4,
   the allowlisted Compose controller.
5. Evidence is normalized and redacted before JSON or HTML reports are written.
6. Run metadata and scenario results are persisted in SQLite; generated
   artifacts remain in the selected artifact directory.

## Safety boundaries

- Target URLs must be local HTTP endpoints.
- External network access is disabled by configuration validation.
- Infrastructure fault injection can address only `app` and `mongo`.
- Compose inspection rejects privileged services, host networking, and Docker
  socket mounts.
- Repository inspection never runs repository scripts.
- Target execution approval is an explicit safety boundary; this MVP does not
  automatically execute arbitrary external repositories.

## Persistence

`runs` stores lifecycle status, configuration path, repository URL, requested
revision, resolved commit, cleanup status, and safety warnings. The
`scenario_results` table stores each result with evidence and reproduction
steps. Every run directory contains `report.json` and `report.html` when report
generation succeeds.
