from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

CWE_ID = re.compile(r"^CWE-\d+$")


def catalog_ids(path: str | Path) -> set[str]:
    """Carga los IDs de debilidad del XML oficial local."""
    root = ET.parse(path).getroot()
    return {
        f"CWE-{weakness.attrib['ID']}"
        for weakness in root.iter()
        if weakness.tag.rsplit("}", 1)[-1] == "Weakness"
        and weakness.attrib.get("ID", "").isdigit()
    }


def validate_cwe(cwe_id: str | None, catalog_path: str | Path | None) -> str | None:
    if not cwe_id:
        return None
    if not CWE_ID.fullmatch(cwe_id):
        raise ValueError(f"Identificador CWE inválido: {cwe_id}")
    if catalog_path is None:
        return cwe_id
    if cwe_id not in catalog_ids(catalog_path):
        raise ValueError(f"El CWE no existe en el catálogo: {cwe_id}")
    return cwe_id
