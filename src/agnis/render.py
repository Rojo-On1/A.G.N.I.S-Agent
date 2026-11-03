from __future__ import annotations

from .models import ReportInput


def render_report(report: ReportInput) -> str:
    draft = report.draft
    lines = [
        "Declaración de confidencialidad",
        "[PENDIENTE: texto de confidencialidad]",
        "",
        "## 1. Resumen ejecutivo",
        "",
        "El informe fue generado a partir de los datos resueltos por A.G.N.I.S.",
        "",
        "## 2. Alcance y reglas de compromiso",
        "",
        f"- **Aplicación:** {draft.application or '[PENDIENTE]'}",
        f"- **URL base:** {draft.base_url or '[PENDIENTE]'}",
        f"- **Entorno:** {draft.environment or '[PENDIENTE]'}",
        "",
        "## 3. Metodología",
        "",
        "La evaluación siguió la metodología OWASP WSTG v4.2.",
        "",
        "## 4. Hallazgos detallados",
    ]
    for resolved in report.findings:
        finding = resolved.finding
        classification = resolved.classification
        lines.extend(
            [
                "",
                f"### {finding.id} — {finding.title}",
                "",
                f"**Activo / endpoint:** {finding.asset or '[PENDIENTE]'}",
                "",
                "#### Descripción",
                finding.title,
                "",
                "#### Clasificación técnica",
                f"- **OWASP:** {classification.owasp_category}",
                f"- **Causa:** {classification.technical_cause}",
                f"- **CWE:** {classification.cwe_id or '[PENDIENTE: selección CWE]'}",
                f"- **Vector CVSS:** {classification.cvss_vector}",
                "",
                "#### Impacto demostrado",
            ]
        )
        lines.extend(f"- {item}" for item in resolved.impact.impact)
        lines.extend(["", "#### Remediación"])
        lines.extend(f"- {item}" for item in resolved.impact.recommendations)
    lines.extend(["", "## Anexo — Glosario", "[PENDIENTE: glosario]"])
    return "\n".join(lines) + "\n"
