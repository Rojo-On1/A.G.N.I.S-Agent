from __future__ import annotations

from .models import Finding, Observation, PocResult


class PocRunner:
    """Execution boundary for real browser/Burp integrations.

    The MVP does not pretend to execute web requests. Callers may provide a JSON
    result later; unexecuted steps remain unconfirmed and cannot feed impact.
    """

    def run(self, finding: Finding) -> PocResult:
        return PocResult(
            finding_id=finding.id,
            observations=[
                Observation(step_number=step.number, confirmed=False)
                for step in finding.steps
            ],
            gaps=["No hay adaptador de ejecución configurado para este hallazgo."],
        )
