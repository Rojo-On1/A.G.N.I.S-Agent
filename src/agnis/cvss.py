from __future__ import annotations

from cvss import CVSS4


def score_vector(vector: str) -> float:
    """Calcula la puntuación CVSS 4.0; nunca acepta una puntuación del modelo."""
    try:
        score = CVSS4(vector).scores()[0]
    except Exception as exc:
        raise ValueError(f"Vector CVSS 4.0 inválido: {vector}") from exc
    return float(score)


def severity_for_score(score: float) -> str:
    if score == 0:
        return "None"
    if score < 4:
        return "Low"
    if score < 7:
        return "Medium"
    if score < 9:
        return "High"
    return "Critical"
