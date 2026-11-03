from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from .models import Finding, Observation, PocResult

_SENSITIVE = re.compile(r"(authorization|cookie|token|password|secret|api[-_]?key)", re.I)


class HttpStep(BaseModel):
    step_number: int
    path: str
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    expected_status: int | None = None


def _redact(value: str) -> str:
    if not value:
        return value
    return re.sub(
        r'("(?:authorization|cookie|token|password|secret|api[-_]?key)"\s*:\s*)"[^"]*"',
        r'\1"[REDACTADO]"',
        value,
        flags=re.I,
    )


def _safe_headers(headers: Mapping[str, str]) -> list[str]:
    return [
        f"{name}: {_redact(value) if _SENSITIVE.search(name) else value}"
        for name, value in headers.items()
    ]


class HttpPocRunner:
    """Runs explicitly supplied HTTP requests against one authorized base URL."""

    def __init__(
        self,
        base_url: str,
        specs: Mapping[str, list[HttpStep]],
        timeout: float = 10.0,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url debe ser una URL HTTP(S) válida")
        self.base_url = base_url.rstrip("/") + "/"
        self._host = parsed.netloc
        self.specs = specs
        self.timeout = timeout

    @classmethod
    def from_json(cls, base_url: str, path: str) -> "HttpPocRunner":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        specs = {
            finding_id: [HttpStep.model_validate(item) for item in items]
            for finding_id, items in raw.items()
        }
        return cls(base_url, specs)

    def run(self, finding: Finding) -> PocResult:
        observations: list[Observation] = []
        gaps: list[str] = []
        for step in finding.steps:
            spec = next(
                (item for item in self.specs.get(finding.id, []) if item.step_number == step.number),
                None,
            )
            if spec is None:
                observations.append(Observation(step_number=step.number))
                gaps.append(f"Falta configuración HTTP para el paso {step.number}.")
                continue
            target = urljoin(self.base_url, spec.path.lstrip("/"))
            if urlparse(target).netloc != self._host:
                raise ValueError(f"El paso {step.number} intenta salir del host autorizado")
            request = Request(
                target,
                data=spec.body.encode() if spec.body is not None else None,
                headers=spec.headers,
                method=spec.method.upper(),
            )
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    body = response.read(64 * 1024).decode("utf-8", errors="replace")
                    status = response.status
                    fields = list(json.loads(body).keys()) if body.lstrip().startswith("{") else []
                    observations.append(
                        Observation(
                            step_number=step.number,
                            http_status=status,
                            fields=fields,
                            observed_values=_redact(body[:1000]),
                            confirmed=(
                                spec.expected_status is not None
                                and status == spec.expected_status
                            ),
                        )
                    )
            except HTTPError as error:
                observations.append(
                    Observation(
                        step_number=step.number,
                        http_status=error.code,
                        error=str(error),
                        confirmed=spec.expected_status == error.code,
                    )
                )
            except URLError as error:
                observations.append(
                    Observation(step_number=step.number, error=str(error.reason))
                )
        return PocResult(finding_id=finding.id, observations=observations, gaps=gaps)
