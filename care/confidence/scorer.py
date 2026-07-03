from __future__ import annotations
from datetime import datetime, timezone

RELIABILITY_WEIGHTS: dict[str, float] = {
    "official_documentation": 0.95,
    "official_table": 0.90,
    "research_paper": 0.85,
    "news_article": 0.70,
    "synthetic_demo": 0.60,
    "image_ocr": 0.55,
    "unknown": 0.50,
}


def source_reliability(source_type: str) -> float:
    return RELIABILITY_WEIGHTS.get(source_type, 0.50)


def freshness_score(publication_date: str | None) -> float:
    if not publication_date:
        return 0.5
    try:
        pub = datetime.fromisoformat(publication_date)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - pub).days
        if age_days <= 30:
            return 1.0
        if age_days <= 365:
            return 0.8
        if age_days <= 3 * 365:
            return 0.6
        return 0.4
    except (ValueError, TypeError):
        return 0.5
