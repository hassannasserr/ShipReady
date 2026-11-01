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
