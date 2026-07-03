from __future__ import annotations
from care.jury.models import EvidenceObject
from care.confidence.scorer import source_reliability


def ingest_image(
    source_id: str,
    path: str,
    metadata: dict | None = None,
) -> list[EvidenceObject]:
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return []
    metadata = metadata or {}
    source_type = metadata.get("source_type", "image_ocr")
    reliability = source_reliability(source_type)
    img = Image.open(path)
    text = pytesseract.image_to_string(img).strip()
    if not text:
        return []
    return [
        EvidenceObject(
            source_id=f"{source_id}::ocr",
            source_type=source_type,
            content=text,
            metadata=metadata,
            reliability_score=reliability,
        )
    ]
