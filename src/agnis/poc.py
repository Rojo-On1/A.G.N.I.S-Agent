from __future__ import annotations

from collections.abc import Mapping

from .models import Finding, Observation, PocResult


class PocRunner:
    """Execution boundary for real browser/Burp integrations.

    The MVP does not pretend to execute web requests. Callers may provide a JSON
    result later; unexecuted steps remain unconfirmed and cannot feed impact.
    """

    def run(
        self, finding: Finding, supplied: Mapping[int, Observation] | None = None
    ) -> PocResult:
        supplied = supplied or {}
        return PocResult(
            finding_id=finding.id,
            observations=[
                supplied.get(step.number, Observation(step_number=step.number))
                for step in finding.steps
            ],
            gaps=(
                []
                if supplied
                else ["No hay adaptador de ejecución configurado para este hallazgo."]
            ),
        )
