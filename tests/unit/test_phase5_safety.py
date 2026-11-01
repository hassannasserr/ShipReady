from pathlib import Path

import pytest

from shipready.adapters.github_adapter import RepositoryError, validate_github_url
from shipready.safety.cleanup import CleanupError, cleanup_workspace
from shipready.safety.policy import SafetyViolation, inspect_compose_safety


@pytest.mark.parametrize(
    "value",
    [
        "http://github.com/acme/project",
        "https://github.com/acme/project?token=secret",
        "https://evil.example/acme/project",
    ],
)
def test_unsafe_github_urls_are_rejected(value: str) -> None:
    with pytest.raises(RepositoryError):
        validate_github_url(value)


def test_github_url_is_normalized() -> None:
    assert validate_github_url("https://github.com/acme/project") == (
        "https://github.com/acme/project.git"
    )


def test_compose_socket_mount_is_rejected(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        "services:\n  app:\n    volumes:\n      - /var/run/docker.sock:/sock\n",
        encoding="utf-8",
    )

    with pytest.raises(SafetyViolation, match="Docker socket"):
        inspect_compose_safety(compose)


def test_compose_host_database_port_is_rejected(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yaml"
    compose.write_text(
        "services:\n"
        "  mongo:\n"
        "    image: mongo:7\n"
        "    ports: ['27017:27017']\n"
        "  app:\n"
        "    image: app\n"
        "    ports: ['127.0.0.1:3000:3000']\n"
        "networks:\n"
        "  demo-internal:\n"
        "    internal: true\n",
        encoding="utf-8",
    )

    with pytest.raises(SafetyViolation, match="mongo"):
        inspect_compose_safety(compose)


def test_cleanup_requires_run_marker(tmp_path: Path) -> None:
    workspace = tmp_path / "run"
    workspace.mkdir()

    with pytest.raises(CleanupError, match="unmarked"):
        cleanup_workspace(workspace, tmp_path)
