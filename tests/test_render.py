from agnis.models import (
    Finding,
    ImpactRecommendation,
    NormalizedDraft,
    PocResult,
    ReportInput,
    ResolvedFinding,
    TechnicalClassification,
)
from agnis.render import render_report


def test_render_report_includes_finding_data() -> None:
    report = ReportInput(
        draft=NormalizedDraft(application="Demo"),
        findings=[
            ResolvedFinding(
                finding=Finding(id="FF-001", title="Fallo", asset="/api"),
                poc=PocResult(finding_id="FF-001"),
                classification=TechnicalClassification(
                    cvss_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N",
                    owasp_category="A01",
                    technical_cause="Autorización ausente",
                ),
                impact=ImpactRecommendation(
                    impact=["La respuesta contiene el campo indicado (paso 1)."],
                    recommendations=["Validar autorización en el servidor."],
                ),
            )
        ],
    )
    output = render_report(report)
    assert "FF-001 — Fallo" in output
    assert "Validar autorización en el servidor." in output
