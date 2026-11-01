from pathlib import Path

import pytest

from shipready.agent.config import load_config


def test_demo_config_loads() -> None:
    config = load_config(Path("configs/demo-project.yaml"))

    assert config.project.name == "demo-commerce"
    assert config.execution.allow_external_network is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("base_url", "https://example.com"),
        ("database.disposable_test_database", False),
        ("execution.allow_external_network", True),
    ],
)
def test_unsafe_config_is_rejected(tmp_path, field: str, value: object) -> None:
    source = Path("configs/demo-project.yaml").read_text(encoding="utf-8")
    if field == "base_url":
        source = source.replace("http://127.0.0.1:3000", str(value))
    elif field == "database.disposable_test_database":
        source = source.replace(
            "disposable_test_database: true",
            "disposable_test_database: false",
        )
    else:
        source = source.replace(
            "allow_external_network: false",
            "allow_external_network: true",
        )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(source, encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(config_path)
