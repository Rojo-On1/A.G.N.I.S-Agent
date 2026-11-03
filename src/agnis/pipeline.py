from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agents import build_agents, classify, normalize, write_impact
from .artifacts import save_report_artifacts
from .cvss import score_vector, severity_for_score
from .cwe import validate_cwe
from .models import ImpactRecommendation, Observation, ReportInput
from .poc import PocRunner
from .poc_http import HttpPocRunner
from .render import render_template
from .validation import validate_final_report


def run_pipeline(
    draft_markdown: str,
    template_path: str,
    output_pdf: str,
    poc_results_path: str | None = None,
    cwe_catalog_path: str | None = None,
    poc_http_spec_path: str | None = None,
    artifacts_dir: str | None = None,
    allow_network: bool = False,
) -> str:
    if poc_http_spec_path and not allow_network:
        raise ValueError("El adaptador HTTP requiere --allow-network explícito.")
    normalizer, classifier, impact_agent = build_agents()
    draft = normalize(normalizer, draft_markdown)
    http_runner = (
        HttpPocRunner.from_json(draft.base_url or "", poc_http_spec_path)
        if poc_http_spec_path
        else None
    )
    poc_runner = PocRunner()
    supplied_results = _load_poc_results(poc_results_path)
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
        classification = classify(classifier, finding)
        classification.cvss_score = score_vector(classification.cvss_vector)
        classification.severity = severity_for_score(classification.cvss_score)
        classification.cwe_id = validate_cwe(
            classification.cwe_id, cwe_catalog_path
        )
        confirmed_steps = [
            {
                "number": observation.step_number,
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
    if artifacts_dir:
        save_report_artifacts(report, artifacts_dir)
    render_template(report, template_path, output_pdf)
    validate_final_report(report, output_pdf)
    return output_pdf


def _load_poc_results(path: str | None) -> dict[str, dict[int, Observation]]:
    if path is None:
        return {}
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"No existe el resultado POC: {source}")
    raw: dict[str, list[dict[str, Any]]] = json.loads(source.read_text(encoding="utf-8"))
    return {
        finding_id: {
            int(item["step_number"]): Observation.model_validate(item)
            for item in observations
        }
        for finding_id, observations in raw.items()
    }
