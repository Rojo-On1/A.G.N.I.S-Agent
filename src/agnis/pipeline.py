from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Callable

from .agents import build_agents, classify, normalize, write_impact
from .artifacts import save_report_artifacts
from .cvss import score_vector, severity_for_score
from .cwe import validate_cwe
from .models import Finding, ImpactRecommendation, NormalizedDraft, Observation, ReportInput
from .poc import PocRunner
from .poc_http import HttpPocRunner
from .render import render_template
from .validation import validate_final_report

NormalizationReview = Callable[[NormalizedDraft], bool]
FinalReview = Callable[[ReportInput, str], bool]
HTTP_STATUS = re.compile(r"\bHTTP\s+(\d{3})\b", re.IGNORECASE)


def run_pipeline(
    draft_markdown: str,
    template_path: str,
    output_pdf: str,
    poc_results_path: str | None = None,
    cwe_catalog_path: str | None = None,
    poc_http_spec_path: str | None = None,
    artifacts_dir: str | None = None,
    allow_network: bool = False,
    review_normalization: NormalizationReview | None = None,
    review_final: FinalReview | None = None,
) -> str:
    if poc_http_spec_path and not allow_network:
        raise ValueError("El adaptador HTTP requiere --allow-network explícito.")
    if review_normalization is None or review_final is None:
        raise ValueError("Se requieren revisiones humanas de la normalización y del PDF final.")
    normalizer, classifier, impact_agent = build_agents()
    draft = normalize(normalizer, draft_markdown)
    finding_ids = [finding.id for finding in draft.findings]
    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError("La normalización contiene identificadores de hallazgo duplicados.")
    if not review_normalization(draft):
        raise ValueError("La normalización no fue aprobada por el auditor.")
    http_runner = (
        HttpPocRunner.from_json(draft.base_url or "", poc_http_spec_path)
        if poc_http_spec_path
        else None
    )
    poc_runner = PocRunner()
    supplied_results = _load_poc_results(poc_results_path)
    unknown_ids = set(supplied_results) - {finding.id for finding in draft.findings}
    if unknown_ids:
        raise ValueError(f"Hay resultados POC para hallazgos desconocidos: {', '.join(sorted(unknown_ids))}")
    if cwe_catalog_path is None:
        default_catalog = Path("data/cwec_v5.0.xml")
        cwe_catalog_path = str(default_catalog) if default_catalog.is_file() else None
    resolved = []
    for finding in draft.findings:
        poc = (
            http_runner.run(finding)
            if http_runner
            else poc_runner.run(finding, supplied_results.get(finding.id))
        )
        _validate_observations(finding, poc.observations)
        classification = classify(classifier, finding, draft.exposure)
        classification.cvss_score = score_vector(classification.cvss_vector)
        classification.severity = severity_for_score(classification.cvss_score)
        classification.cwe_id = validate_cwe(
            classification.cwe_id, cwe_catalog_path
        )
        steps_by_number = {step.number: step for step in finding.steps}
        confirmed_steps = [
            {
                "number": observation.step_number,
                "step": steps_by_number[observation.step_number].model_dump(mode="json"),
                "observation": observation.model_dump(mode="json"),
            }
            for observation in poc.observations
            if observation.confirmed
        ]
        impact = (
            write_impact(impact_agent, finding, confirmed_steps)
            if confirmed_steps
            else ImpactRecommendation()
        )
        resolved.append(
            {
                "finding": finding,
                "poc": poc,
                "classification": classification,
                "impact": impact,
            }
        )
    report = ReportInput(draft=draft, findings=resolved)
    output = Path(output_pdf)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="agnis-review-", dir=output.parent) as directory:
        candidate = Path(directory) / "candidate.pdf"
        render_template(report, template_path, str(candidate))
        validate_final_report(report, candidate)
        if not review_final(report, str(candidate)):
            raise ValueError("El PDF final no fue aprobado por el auditor.")
        candidate.replace(output)
    if artifacts_dir:
        save_report_artifacts(report, artifacts_dir)
    return output_pdf


def _validate_observations(finding: Finding, observations: list[Observation]) -> None:
    if not finding.steps:
        raise ValueError(f"El hallazgo {finding.id} no contiene pasos verificables.")
    steps = {step.number: step for step in finding.steps}
    if len(steps) != len(finding.steps):
        raise ValueError(f"Hay números de paso duplicados en {finding.id}.")
    if len(observations) != len(finding.steps):
        raise ValueError(f"Faltan o sobran observaciones en {finding.id}.")
    seen: set[int] = set()
    for observation in observations:
        number = observation.step_number
        if number not in steps or number in seen:
            raise ValueError(f"Observación con paso desconocido o duplicado en {finding.id}: {number}.")
        seen.add(number)
        if not observation.confirmed:
            continue
        expected = steps[number].expected_result
        if not expected or expected.startswith("[PENDIENTE"):
            raise ValueError(f"No puede confirmarse el paso {number} sin resultado esperado.")
        expected_status = HTTP_STATUS.search(expected)
        if expected_status and observation.http_status != int(expected_status.group(1)):
            raise ValueError(f"El estado HTTP observado contradice el esperado en {finding.id}, paso {number}.")
        if observation.error and observation.http_status is None:
            raise ValueError(f"No puede confirmarse el paso {number} con un error registrado.")


def _load_poc_results(path: str | None) -> dict[str, dict[int, Observation]]:
    if path is None:
        return {}
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"No existe el resultado POC: {source}")
    raw: dict[str, list[dict[str, Any]]] = json.loads(source.read_text(encoding="utf-8"))
    result: dict[str, dict[int, Observation]] = {}
    for finding_id, observations in raw.items():
        by_step: dict[int, Observation] = {}
        for item in observations:
            observation = Observation.model_validate(item)
            number = observation.step_number
            if number in by_step:
                raise ValueError(f"Resultado POC duplicado en {finding_id}, paso {number}.")
            by_step[number] = observation
        result[finding_id] = by_step
    return result
