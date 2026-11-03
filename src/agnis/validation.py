from __future__ import annotations

from pathlib import Path

import fitz

from .models import ReportInput


def validate_final_report(report: ReportInput, output_pdf: str | Path) -> None:
    if not report.findings:
        raise ValueError("No se puede generar un informe sin hallazgos.")
    for finding in report.findings:
        if finding.classification.cvss_score is None:
            raise ValueError(f"Falta puntuación CVSS para {finding.finding.id}.")
        if "{{" in finding.finding.title:
            raise ValueError(f"El título contiene un marcador sin resolver: {finding.finding.id}.")
    output = Path(output_pdf)
    if not output.is_file() or output.stat().st_size == 0:
        raise ValueError("La salida PDF no fue generada.")
    document = fitz.open(output)
    text = "\n".join(page.get_text() for page in document)
    document.close()
    if "{{" in text:
        raise ValueError("La plantilla contiene marcadores sin resolver.")
