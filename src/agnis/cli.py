from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import NormalizedDraft, ReportInput
from .pipeline import run_pipeline


def _review_normalization(draft: NormalizedDraft) -> bool:
    print("\nNormalización propuesta:")
    print(json.dumps(draft.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return input("¿Apruebas esta normalización? [s/N] ").strip().lower() == "s"


def _review_final(report: ReportInput, candidate_pdf: str) -> bool:
    print(f"\nPDF candidato para revisión: {candidate_pdf}")
    print(f"Hallazgos: {len(report.findings)}")
    return input("Tras revisar el PDF, ¿apruebas su publicación? [s/N] ").strip().lower() == "s"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un informe PDF A.G.N.I.S. desde borrador y plantilla."
    )
    parser.add_argument("draft", type=Path, help="Ruta del borrador Markdown")
    parser.add_argument(
        "template", type=Path, help="Plantilla institucional .docx o .pdf"
    )
    parser.add_argument(
        "--poc-results",
        type=Path,
        help="JSON de observaciones confirmadas por un adaptador POC",
    )
    parser.add_argument(
        "--cwe-catalog",
        type=Path,
        help="Ruta local a cwec_v5.0.xml para validar CWE",
    )
    parser.add_argument(
        "--poc-http-spec",
        type=Path,
        help="JSON de peticiones HTTP explícitas por hallazgo y paso",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Permite al adaptador HTTP ejecutar peticiones al host del borrador",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        help="Directorio para guardar el JSON de resultados resueltos",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("informe-agnis.pdf"),
        help="Ruta del informe PDF de salida",
    )
    args = parser.parse_args()
    result = run_pipeline(
        args.draft.read_text(encoding="utf-8"),
        str(args.template),
        str(args.output),
        str(args.poc_results) if args.poc_results else None,
        str(args.cwe_catalog) if args.cwe_catalog else None,
        str(args.poc_http_spec) if args.poc_http_spec else None,
        str(args.artifacts_dir) if args.artifacts_dir else None,
        args.allow_network,
        review_normalization=_review_normalization,
        review_final=_review_final,
    )
    print(result)
