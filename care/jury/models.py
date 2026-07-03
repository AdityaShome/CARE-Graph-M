from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal


ClaimType = Literal["numeric_fact", "factual", "formula", "generic", "verb_style"]

Relation = Literal[
    "supported",
    "contradicted",
    "partially_supported",
    "unsupported",
    "ambiguous",
    "needs_review",
    "blocked",
    "unresolvable",
]

OverallVerdict = Literal["APPROVED", "FLAGGED", "NEEDS_REVIEW", "BLOCKED", "UNRESOLVABLE"]


@dataclass
class Claim:
    text: str
    claim_type: ClaimType = "generic"
    entity: str = ""
    metric: str = ""
    value: float | None = None
    unit: str | None = None
    time_period: str | None = None
    safety_sensitive: bool = False


@dataclass
class EvidenceObject:
    source_id: str
    source_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    reliability_score: float = 0.5
    numeric_value: float | None = None
    metric: str = ""
    entity: str = ""
    time_period: str | None = None


@dataclass
class ConfidenceVector:
    source_reliability: float = 0.5
    freshness: float = 0.5
    extraction_quality: float = 0.5
    corroboration: float = 0.5
    math_validity: float = 0.5
    semantic_alignment: float = 0.5

    def scalar(self) -> float:
        weights = [0.25, 0.10, 0.15, 0.15, 0.20, 0.15]
        values = [
            self.source_reliability,
            self.freshness,
            self.extraction_quality,
            self.corroboration,
            self.math_validity,
            self.semantic_alignment,
        ]
        return sum(w * v for w, v in zip(weights, values))

    def to_dict(self) -> dict:
        return {
            "source_reliability": self.source_reliability,
            "freshness": self.freshness,
            "extraction_quality": self.extraction_quality,
            "corroboration": self.corroboration,
            "math_validity": self.math_validity,
            "semantic_alignment": self.semantic_alignment,
            "scalar": self.scalar(),
        }


@dataclass
class ClaimVerdict:
    claim: Claim
    relation: Relation
    evidence_used: list[EvidenceObject] = field(default_factory=list)
    confidence: ConfidenceVector = field(default_factory=ConfidenceVector)
    correction: str | None = None
    math_validity: float = 0.5
    reasoning_score: float = 0.5


@dataclass
class JuryVerdict:
    overall: OverallVerdict
    claim_verdicts: list[ClaimVerdict]
    raw_answer: str
    governed_answer: str
    audit_id: str = ""
    confidence_scalar: float = 0.5
