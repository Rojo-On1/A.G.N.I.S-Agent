from __future__ import annotations

import json

from .llm import StructuredAgent
from .models import (
    Finding,
    ImpactRecommendation,
    NormalizedDraft,
    TechnicalClassification,
)

NORMALIZER_PROMPT = """Eres el Normalizador de A.G.N.I.S.
Convierte el borrador en datos estructurados. Conserva literalmente las acciones.
No inventes resultados, cuentas, hallazgos ni datos faltantes: registra lo que falte
en pending o ambiguities. No calcules severidad, CVSS ni impacto."""

CLASSIFIER_PROMPT = """Eres el Clasificador técnico de A.G.N.I.S.
Propón un vector CVSS 4.0, una categoría OWASP Top 10 válida y una causa técnica
basándote solo en el hallazgo y sus pasos. No calcules la puntuación ni la severidad.
No inventes un CWE: si no se proporciona un catálogo de candidatos, deja cwe_id vacío."""

IMPACT_PROMPT = """Eres el agente de Impacto y Recomendaciones de A.G.N.I.S.
Describe únicamente lo que demuestran los pasos confirmados. Cada impacto debe
referenciar el número del paso. Las recomendaciones deben atender la causa observada.
No agregues consecuencias no demostradas ni severidades."""


def build_agents(model: object) -> tuple[StructuredAgent, StructuredAgent, StructuredAgent]:
    return (
        StructuredAgent(model, NORMALIZER_PROMPT, NormalizedDraft),
        StructuredAgent(model, CLASSIFIER_PROMPT, TechnicalClassification),
        StructuredAgent(model, IMPACT_PROMPT, ImpactRecommendation),
    )


def normalize(agent: StructuredAgent, draft_markdown: str) -> NormalizedDraft:
    return agent.invoke(draft_markdown)


def classify(agent: StructuredAgent, finding: Finding) -> TechnicalClassification:
    return agent.invoke(json.dumps(finding.model_dump(mode="json"), ensure_ascii=False))


def write_impact(
    agent: StructuredAgent, finding: Finding, confirmed_steps: list[dict[str, object]]
) -> ImpactRecommendation:
    payload = {
        "finding": finding.model_dump(mode="json"),
        "confirmed_steps": confirmed_steps,
    }
    return agent.invoke(json.dumps(payload, ensure_ascii=False))
