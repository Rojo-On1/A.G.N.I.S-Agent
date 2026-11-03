from __future__ import annotations

from .agents import build_agents, classify, normalize, write_impact
from .llm import create_openai_model
from .models import ReportInput
from .poc import PocRunner
from .render import render_template


def run_pipeline(draft_markdown: str, template_path: str, output_pdf: str) -> str:
    model = create_openai_model()
    normalizer, classifier, impact_agent = build_agents(model)
    draft = normalize(normalizer, draft_markdown)
    poc_runner = PocRunner()
    resolved = []
    for finding in draft.findings:
        poc = poc_runner.run(finding)
        classification = classify(classifier, finding)
        confirmed_steps = [
            {
                "number": observation.step_number,
                "observation": observation.model_dump(mode="json"),
            }
            for observation in poc.observations
            if observation.confirmed
        ]
        impact = write_impact(impact_agent, finding, confirmed_steps)
        resolved.append(
            {
                "finding": finding,
                "poc": poc,
                "classification": classification,
                "impact": impact,
            }
        )
    report = ReportInput(draft=draft, findings=resolved)
    render_template(report, template_path, output_pdf)
    return output_pdf
