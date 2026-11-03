from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un informe A.G.N.I.S. desde un borrador Markdown."
    )
    parser.add_argument("draft", type=Path, help="Ruta del borrador Markdown")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("informe-agnis.md"),
        help="Ruta del informe de salida",
    )
    args = parser.parse_args()
    result = run_pipeline(args.draft.read_text(encoding="utf-8"))
    args.output.write_text(result, encoding="utf-8")
    print(args.output)
