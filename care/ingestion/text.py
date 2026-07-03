from __future__ import annotations
import re
from care.jury.models import EvidenceObject
from care.confidence.scorer import source_reliability


def ingest_text(
    source_id: str,
    text: str,
    metadata: dict | None = None,
    chunk_size: int = 300,
) -> list[EvidenceObject]:
    metadata = metadata or {}
    source_type = metadata.get("source_type", "unknown")
    reliability = source_reliability(source_type)
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current = ""
    for s in sentences:
        if len(current) + len(s) < chunk_size:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return [
        EvidenceObject(
            source_id=f"{source_id}::chunk{i}",
            source_type=source_type,
            content=chunk,
            metadata=metadata,
            reliability_score=reliability,
        )
        for i, chunk in enumerate(chunks)
    ]
