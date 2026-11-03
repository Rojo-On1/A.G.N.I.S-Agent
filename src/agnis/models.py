from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Step(BaseModel):
    number: int
    action: str
    account: str | None = None
    expected_result: str | None = None


class Finding(BaseModel):
    id: str
    title: str
    asset: str | None = None
    required_role: str | None = None
    wstg_category: str | None = None
    steps: list[Step] = Field(default_factory=list)


class NormalizedDraft(BaseModel):
    application: str | None = None
    base_url: str | None = None
    environment: Literal["production", "staging"] | None = None
    test_date: str | None = None
    exposure: Literal["public", "internal"] | None = None
    findings: list[Finding] = Field(default_factory=list)
    pending: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class Observation(BaseModel):
    step_number: int
    http_status: int | None = None
    fields: list[str] = Field(default_factory=list)
    observed_values: str | None = None
    confirmed: bool = False


class PocResult(BaseModel):
    finding_id: str
    observations: list[Observation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    capture_path: str | None = None


class TechnicalClassification(BaseModel):
    cvss_vector: str
    owasp_category: str
    technical_cause: str
    cwe_id: str | None = None


class ImpactRecommendation(BaseModel):
    impact: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ResolvedFinding(BaseModel):
    finding: Finding
    poc: PocResult
    classification: TechnicalClassification
    impact: ImpactRecommendation


class ReportInput(BaseModel):
    draft: NormalizedDraft
    findings: list[ResolvedFinding] = Field(default_factory=list)
