from pathlib import Path

import pytest

from agnis.cvss import score_vector, severity_for_score
from agnis.cwe import catalog_ids, validate_cwe


VECTOR = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N"


def test_cvss_score_and_severity_are_deterministic() -> None:
    score = score_vector(VECTOR)
    assert score == 6.9
    assert severity_for_score(score) == "Medium"


def test_cwe_validation_uses_catalog(tmp_path: Path) -> None:
    catalog = tmp_path / "cwec_v5.0.xml"
    catalog.write_text(
        '<Weakness_Catalog><Weaknesses><Weakness ID="862"/></Weaknesses></Weakness_Catalog>',
        encoding="utf-8",
    )
    assert catalog_ids(catalog) == {"CWE-862"}
    assert validate_cwe("CWE-862", catalog) == "CWE-862"
    with pytest.raises(ValueError):
        validate_cwe("CWE-863", catalog)
