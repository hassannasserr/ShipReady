from pathlib import Path

import pytest

from shipready.engines.infrastructure.controller import ComposeController


def test_compose_controller_rejects_unapproved_service() -> None:
    controller = ComposeController(Path("docker/compose.yaml"), timeout=1)

    with pytest.raises(ValueError, match="not approved"):
        controller.stop("database")


def test_compose_controller_rejects_negative_delay() -> None:
    controller = ComposeController(Path("docker/compose.yaml"), timeout=1)

    with pytest.raises(ValueError, match="between 0 and 30000"):
        controller.set_delay(-1)


def test_compose_controller_uses_owned_project_name() -> None:
    controller = ComposeController(Path("docker/compose.yaml"), timeout=1)

    assert controller.PROJECT_NAME == "shipready-demo"


def test_compose_controller_rejects_unowned_project(monkeypatch) -> None:
    controller = ComposeController(Path("docker/compose.yaml"), timeout=1)
    outputs = iter(["app\nmongo\n", ""])
    monkeypatch.setattr(controller, "_run", lambda *args, **kwargs: next(outputs))

    with pytest.raises(RuntimeError, match="not running or owned"):
        controller.verify_project_ownership()
