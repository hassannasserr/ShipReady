from pathlib import Path

import httpx

from shipready.agent.config import load_config
from shipready.engines.baseline.runner import run_baseline


def test_baseline_records_real_health_response(monkeypatch) -> None:
    config = load_config(Path("configs/demo-project.yaml"))
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: httpx.Response(
            200,
            request=httpx.Request("GET", "http://127.0.0.1:3000/health"),
            text='{"status":"healthy"}',
        ),
    )

    result = run_baseline(config)

    assert result.status == "passed"
    assert any(
        item.name == "status_code" and item.value == 200
        for item in result.evidence
    )
