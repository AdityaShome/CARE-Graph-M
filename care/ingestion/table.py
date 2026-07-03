from __future__ import annotations
import csv
import io
from care.jury.models import EvidenceObject
from care.confidence.scorer import source_reliability


def ingest_table(
    source_id: str,
    rows: list[dict],
    metadata: dict | None = None,
) -> list[EvidenceObject]:
    metadata = metadata or {}
    source_type = metadata.get("source_type", "official_table")
    reliability = source_reliability(source_type)
    objects: list[EvidenceObject] = []
    for i, row in enumerate(rows):
        content = ", ".join(f"{k}={v}" for k, v in row.items())
        numeric_value: float | None = None
        metric = ""
        for k, v in row.items():
            try:
                numeric_value = float(v)
                metric = k
                break
            except (ValueError, TypeError):
                pass
        objects.append(
            EvidenceObject(
                source_id=f"{source_id}::row{i}",
                source_type=source_type,
                content=content,
                metadata={**metadata, "row": row},
                reliability_score=reliability,
                numeric_value=numeric_value,
                metric=metric,
            )
        )
    return objects


def ingest_csv(
    source_id: str,
    path: str,
    metadata: dict | None = None,
) -> list[EvidenceObject]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return ingest_table(source_id, rows, metadata)
