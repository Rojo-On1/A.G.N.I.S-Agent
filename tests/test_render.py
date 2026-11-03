from pathlib import Path

import fitz

from agnis.models import (
    Finding,
    ImpactRecommendation,
    NormalizedDraft,
    PocResult,
    ReportInput,
    ResolvedFinding,
    TechnicalClassification,
)
from agnis.render import render_template


def test_render_pdf_template(tmp_path: Path) -> None:
    template = fitz.open()
    page = template.new_page()
    page.insert_text((72, 72), "{{application}} - {{finding_1.title}}")
    template_path = tmp_path / "template.pdf"
    template.save(template_path)
    template.close()

    report = ReportInput(
        draft=NormalizedDraft(application="Demo"),
        findings=[
            ResolvedFinding(
                finding=Finding(id="FF-001", title="Fallo"),
                poc=PocResult(finding_id="FF-001"),
                classification=TechnicalClassification(
                    cvss_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N",
                    owasp_category="A01",
                    technical_cause="Autorización ausente",
                ),
                impact=ImpactRecommendation(),
            )
        ],
    )
    output = tmp_path / "output.pdf"
    render_template(report, str(template_path), str(output))
    text = "\n".join(page.get_text() for page in fitz.open(output))
    assert "Demo" in text
    assert "Fallo" in text
