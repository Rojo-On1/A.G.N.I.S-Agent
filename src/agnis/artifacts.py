from __future__ import annotations

import json
from pathlib import Path

from .models import ReportInput


def save_report_artifacts(report: ReportInput, directory: str | Path) -> Path:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    path = target / "resolved-report.json"
    path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
