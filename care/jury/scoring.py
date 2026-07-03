from __future__ import annotations
from care.jury.models import ClaimVerdict, ConfidenceVector, EvidenceObject
from care.confidence.scorer import source_reliability, freshness_score


def build_confidence_vector(
    cv: ClaimVerdict,
    evidence_objects: list[EvidenceObject],
) -> ConfidenceVector:
    if not evidence_objects:
        return ConfidenceVector()
    rel = max(o.reliability_score for o in evidence_objects)
    fresh = max(
        freshness_score(o.metadata.get("publication_date"))
        for o in evidence_objects
    )
    corroboration = min(len(evidence_objects) / 3.0, 1.0)
    return ConfidenceVector(
        source_reliability=rel,
        freshness=fresh,
        extraction_quality=0.8 if evidence_objects else 0.3,
        corroboration=corroboration,
        math_validity=cv.math_validity,
        semantic_alignment=cv.reasoning_score,
    )
