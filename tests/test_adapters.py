import json
from pathlib import Path

import pytest

from agnis.models import Finding, Step
from agnis.poc_http import HttpPocRunner


def test_http_runner_rejects_network_without_explicit_opt_in() -> None:
    from agnis.pipeline import run_pipeline

    with pytest.raises(ValueError, match="allow-network"):
        run_pipeline("", "template.pdf", "output.pdf", poc_http_spec_path="spec.json")


def test_http_runner_uses_only_configured_host(tmp_path: Path, monkeypatch) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps({"FF-001": [{"step_number": 1, "path": "/api"}]}),
        encoding="utf-8",
    )
    runner = HttpPocRunner.from_json("https://example.test", str(spec))
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return b'{"ok": true}'

    monkeypatch.setattr("agnis.poc_http.urlopen", lambda request, timeout: Response())
    result = runner.run(
        Finding(id="FF-001", title="test", steps=[Step(number=1, action="GET /api")])
    )
    assert result.observations[0].step_number == 1
    assert result.observations[0].fields == ["ok"]
