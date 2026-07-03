from __future__ import annotations
from care.jury.models import EvidenceObject
from care.confidence.scorer import source_reliability


def ingest_pdf(
    source_id: str,
    path: str,
    metadata: dict | None = None,
) -> list[EvidenceObject]:
    try:
        import pdfplumber
    except ImportError:
        return []
    metadata = metadata or {}
    source_type = metadata.get("source_type", "research_paper")
    reliability = source_reliability(source_type)
    objects: list[EvidenceObject] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue
            objects.append(
                EvidenceObject(
                    source_id=f"{source_id}::page{i+1}",
                    source_type=source_type,
                    content=text,
                    metadata={**metadata, "page": i + 1},
                    reliability_score=reliability,
                )
            )
    return objects
