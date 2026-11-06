import json
from pathlib import Path

import fitz
import pytest
from pydantic import ValidationError

from agnis import pipeline
from agnis.agents import classify, write_impact
from agnis.cwe import validate_cwe
from agnis.models import (
    Finding,
    ImpactRecommendation,
    NormalizedDraft,
    Observation,
    Step,
    TechnicalClassification,
)
from agnis.render import render_template


VECTOR = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N"


def _finding(expected: str = "HTTP 200") -> Finding:
    return Finding(
        id="FF-001",
        title="Demo",
        steps=[Step(number=1, action="GET /demo", expected_result=expected)],
    )


def _template(path: Path, include_impact: bool = True) -> None:
    document = fitz.open()
    page = document.new_page()
    markers = ["{{application}}", "{{finding_1.title}}", "{{finding_1.cvss_score}}"]
    if include_impact:
        markers.append("{{finding_1.impact}}")
    for index, marker in enumerate(markers, start=1):
        page.insert_text((72, 50 + index * 40), marker)
    document.save(path)
    document.close()


def _fake_pipeline(monkeypatch, finding: Finding, impact_text: str = "OK") -> None:
    monkeypatch.setattr(pipeline, "build_agents", lambda: (None, None, None))
    monkeypatch.setattr(
        pipeline,
        "normalize",
        lambda agent, markdown: NormalizedDraft(
            application="Demo local", exposure="public", findings=[finding]
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "classify",
        lambda agent, item, exposure: TechnicalClassification(
            cvss_vector=VECTOR,
            owasp_category="A01",
            technical_cause="Control ausente",
            cwe_id="CWE-862",
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "write_impact",
        lambda agent, item, steps: ImpactRecommendation(impact=[impact_text]),
    )


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    template = tmp_path / "template.pdf"
    _template(template)
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps({"FF-001": [{"step_number": 1, "http_status": 200, "confirmed": True}]}),
        encoding="utf-8",
    )
    catalog = tmp_path / "cwe.xml"
    catalog.write_text(
        '<Weakness_Catalog><Weaknesses><Weakness ID="862"/></Weaknesses></Weakness_Catalog>',
        encoding="utf-8",
    )
    return template, observations, catalog


def test_local_pipeline_moves_only_approved_complete_pdf(tmp_path: Path, monkeypatch) -> None:
    _fake_pipeline(monkeypatch, _finding())
    template, observations, catalog = _inputs(tmp_path)
    output = tmp_path / "output.pdf"
    reviews = []

    def approve_final(report, candidate):
        assert not output.exists()
        with fitz.open(candidate) as document:
            assert "OK" in "\n".join(page.get_text() for page in document)
        reviews.append("final")
        return True

    pipeline.run_pipeline(
        "# Demo",
        str(template),
        str(output),
        poc_results_path=str(observations),
        cwe_catalog_path=str(catalog),
        review_normalization=lambda draft: reviews.append("normalization") or True,
        review_final=approve_final,
    )
    assert output.is_file()
    assert reviews == ["normalization", "final"]


def test_conflicting_observation_cannot_reach_impact(tmp_path: Path, monkeypatch) -> None:
    _fake_pipeline(monkeypatch, _finding("HTTP 404"))
    template, observations, catalog = _inputs(tmp_path)
    output = tmp_path / "output.pdf"
    with pytest.raises(ValueError, match="contradice"):
        pipeline.run_pipeline(
            "# Demo", str(template), str(output),
            poc_results_path=str(observations), cwe_catalog_path=str(catalog),
            review_normalization=lambda draft: True,
            review_final=lambda report, pdf: True,
        )
    assert not output.exists()


def test_unapproved_pdf_is_not_published(tmp_path: Path, monkeypatch) -> None:
    _fake_pipeline(monkeypatch, _finding())
    template, observations, catalog = _inputs(tmp_path)
    output = tmp_path / "output.pdf"
    with pytest.raises(ValueError, match="no fue aprobado"):
        pipeline.run_pipeline(
            "# Demo", str(template), str(output),
            poc_results_path=str(observations), cwe_catalog_path=str(catalog),
            review_normalization=lambda draft: True,
            review_final=lambda report, pdf: False,
        )
    assert not output.exists()


def test_pipeline_requires_both_human_review_gates() -> None:
    with pytest.raises(ValueError, match="revisiones humanas"):
        pipeline.run_pipeline("", "template.pdf", "output.pdf")


def test_classifier_receives_exposure_from_normalized_draft() -> None:
    class SpyAgent:
        def invoke(self, text):
            payload = json.loads(text)
            assert payload["exposure"] == "public"
            assert payload["finding"]["id"] == "FF-001"
            return TechnicalClassification(
                cvss_vector=VECTOR, owasp_category="A01", technical_cause="Demo"
            )

    classify(SpyAgent(), _finding(), "public")


def test_expected_http_error_status_can_be_confirmed() -> None:
    pipeline._validate_observations(
        _finding("HTTP 404"),
        [Observation(step_number=1, http_status=404, error="HTTP Error 404", confirmed=True)],
    )


def test_duplicate_poc_results_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "poc.json"
    source.write_text(json.dumps({"FF-001": [
        {"step_number": 1, "confirmed": True},
        {"step_number": 1, "confirmed": False},
    ]}), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        pipeline._load_poc_results(str(source))


def test_duplicate_finding_ids_are_rejected_before_review(monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "build_agents", lambda: (None, None, None))
    monkeypatch.setattr(
        pipeline, "normalize",
        lambda agent, markdown: NormalizedDraft(findings=[_finding(), _finding()]),
    )
    with pytest.raises(ValueError, match="hallazgo duplicados"):
        pipeline.run_pipeline(
            "", "template.pdf", "output.pdf",
            review_normalization=lambda draft: True,
            review_final=lambda report, pdf: True,
        )


def test_impact_agent_receives_only_confirmed_step_details() -> None:
    finding = Finding(
        id="FF-001", title="Demo",
        steps=[Step(number=1, action="GET /public"), Step(number=2, action="GET /private")],
    )

    class SpyAgent:
        def invoke(self, text):
            payload = json.loads(text)
            assert "steps" not in payload["finding"]
            assert len(payload["confirmed_steps"]) == 1
            assert payload["confirmed_steps"][0]["step"]["action"] == "GET /public"
            return ImpactRecommendation(impact=["Paso 1: respuesta visible."])

    write_impact(SpyAgent(), finding, [{
        "number": 1,
        "step": finding.steps[0].model_dump(mode="json"),
        "observation": Observation(step_number=1, confirmed=True).model_dump(mode="json"),
    }])


def test_invalid_classification_and_unchecked_cwe_are_rejected() -> None:
    with pytest.raises(ValidationError, match="OWASP"):
        TechnicalClassification(cvss_vector=VECTOR, owasp_category="A99", technical_cause="Demo")
    with pytest.raises(ValueError, match="catálogo CWE"):
        validate_cwe("CWE-862", None)


def test_pdf_overflow_fails_instead_of_losing_text(tmp_path: Path) -> None:
    from agnis.models import PocResult, ReportInput, ResolvedFinding

    template = tmp_path / "template.pdf"
    _template(template)
    report = ReportInput(
        draft=NormalizedDraft(application="Demo local"),
        findings=[ResolvedFinding(
            finding=_finding(),
            poc=PocResult(finding_id="FF-001"),
            classification=TechnicalClassification(
                cvss_vector=VECTOR, owasp_category="A01", technical_cause="Demo", cvss_score=6.9
            ),
            impact=ImpactRecommendation(impact=["Un impacto demasiado largo para el marcador del PDF."]),
        )],
    )
    output = tmp_path / "output.pdf"
    with pytest.raises(ValueError, match="no cabe"):
        render_template(report, str(template), str(output))
    assert not output.exists()
