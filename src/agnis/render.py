from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz
from docx import Document

from .models import ReportInput, ResolvedFinding

PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")


def _report_values(report: ReportInput) -> dict[str, str]:
    values = {
        "application": report.draft.application or "",
        "base_url": report.draft.base_url or "",
        "environment": report.draft.environment or "",
        "test_date": report.draft.test_date or "",
        "finding_count": str(len(report.findings)),
    }
    for index, resolved in enumerate(report.findings, start=1):
        prefix = f"finding_{index}"
        values.update(_finding_values(prefix, resolved))
    return values


def _finding_values(prefix: str, resolved: ResolvedFinding) -> dict[str, str]:
    classification = resolved.classification
    finding = resolved.finding
    return {
        f"{prefix}.id": finding.id,
        f"{prefix}.title": finding.title,
        f"{prefix}.asset": finding.asset or "",
        f"{prefix}.owasp": classification.owasp_category,
        f"{prefix}.cause": classification.technical_cause,
        f"{prefix}.cwe": classification.cwe_id or "",
        f"{prefix}.cvss_vector": classification.cvss_vector,
        f"{prefix}.impact": "\n".join(resolved.impact.impact),
        f"{prefix}.recommendations": "\n".join(resolved.impact.recommendations),
    }


def _replace_text(text: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda match: values.get(match.group(1), match.group(0)), text)


def _render_docx(report: ReportInput, template_path: Path, output_pdf: Path) -> None:
    document = Document(template_path)
    values = _report_values(report)
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            run.text = _replace_text(run.text, values)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.text = _replace_text(run.text, values)
    with tempfile.TemporaryDirectory() as directory:
        docx_path = Path(directory) / "report.docx"
        document.save(docx_path)
        _convert_docx_to_pdf(docx_path, output_pdf)


def _convert_docx_to_pdf(docx_path: Path, output_pdf: Path) -> None:
    if shutil.which("libreoffice") is None:
        raise RuntimeError(
            "Para plantillas DOCX se requiere LibreOffice instalado en el sistema."
        )
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_pdf.parent),
            str(docx_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    converted = output_pdf.parent / f"{docx_path.stem}.pdf"
    converted.replace(output_pdf)


def _render_pdf(report: ReportInput, template_path: Path, output_pdf: Path) -> None:
    values = _report_values(report)
    document = fitz.open(template_path)
    for page in document:
        for placeholder in PLACEHOLDER.finditer(page.get_text()):
            key = placeholder.group(1)
            value = values.get(key)
            if value is None:
                continue
            matches = page.search_for(placeholder.group(0))
            for rectangle in matches:
                page.add_redact_annot(rectangle, fill=(1, 1, 1))
                page.apply_redactions()
                page.insert_textbox(rectangle, value, fontsize=9, color=(0, 0, 0))
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_pdf)
    document.close()


def render_template(
    report: ReportInput, template_path: str, output_pdf: str
) -> None:
    template = Path(template_path)
    output = Path(output_pdf)
    if not template.is_file():
        raise FileNotFoundError(f"No existe la plantilla: {template}")
    if template.suffix.lower() == ".docx":
        _render_docx(report, template, output)
    elif template.suffix.lower() == ".pdf":
        _render_pdf(report, template, output)
    else:
        raise ValueError("La plantilla debe ser un archivo .docx o .pdf")
