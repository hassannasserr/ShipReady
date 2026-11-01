# Security Model

ShipReady is intended for controlled, local test environments. It is not a
production testing tool and does not treat a GitHub repository as trusted.

## Repository handling

- Only HTTPS `github.com` repository URLs are accepted.
- Cloning uses an argument list and `git --no-checkout`; repository code is not
  imported or executed during inspection.
- Branches and commit revisions are validated before use.
- The resolved commit SHA is recorded in run metadata and reports.
- Unsupported or unreviewed repositories are rejected.

## Execution boundaries

- Configuration requires a local HTTP target and disables external network
  access.
- The test database must be disposable.
- Compose inspection rejects privileged containers, host/none networking, and
  Docker socket mounts.
- The Phase 4 controller permits only the approved `app` and `mongo` services.
- The target does not receive ShipReady's SQLite database, host credentials, or
  Docker socket through the approved Compose file.
- External target execution requires explicit approval; this MVP performs
  inspection only for external repositories.

## Evidence and cleanup

Authorization, cookies, passwords, tokens, API keys, and bearer values are
redacted before JSON and HTML report output. HTML values are escaped, so report
content cannot become executable markup. Run workspaces are marked and cleanup
refuses to delete anything outside the managed workspace root.

Known limitations: resource limits are currently delegated to Docker Desktop
and the configured scenario timeout; the MVP does not provide a complete
container sandbox or arbitrary-repository execution workflow.
