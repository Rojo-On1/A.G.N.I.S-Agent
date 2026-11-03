from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un informe PDF A.G.N.I.S. desde borrador y plantilla."
    )
    parser.add_argument("draft", type=Path, help="Ruta del borrador Markdown")
    parser.add_argument(
        "template", type=Path, help="Plantilla institucional .docx o .pdf"
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
    )
    print(result)
