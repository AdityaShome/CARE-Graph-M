from __future__ import annotations
from care.jury.models import EvidenceObject
from care.confidence.scorer import source_reliability


def parse_evidence(sources: list[dict]) -> list[EvidenceObject]:
    objects: list[EvidenceObject] = []
    for src in sources:
        source_type = src.get("source_type", "unknown")
        source_id = src.get("source_name", "inline") or "inline"
        reliability = source_reliability(source_type)
        meta = {k: v for k, v in src.items() if k not in ("table", "text", "rows")}

        if "table" in src:
            from care.ingestion.table import ingest_table
            rows = src["table"]
            if isinstance(rows, list):
                objects.extend(ingest_table(source_id, rows, meta))

        elif "rows" in src:
            from care.ingestion.table import ingest_table
            objects.extend(ingest_table(source_id, src["rows"], meta))

        elif "text" in src:
            from care.ingestion.text import ingest_text
            objects.extend(ingest_text(source_id, src["text"], meta))

        elif "pdf_path" in src:
            from care.ingestion.pdf import ingest_pdf
            objects.extend(ingest_pdf(source_id, src["pdf_path"], meta))

        elif "image_path" in src:
            from care.ingestion.image import ingest_image
            objects.extend(ingest_image(source_id, src["image_path"], meta))

    return objects
