from __future__ import annotations
from dataclasses import dataclass, field
from care.jury.models import EvidenceObject, Claim, OverallVerdict


@dataclass
class ClaimNode:
    claim_id: str
    claim: Claim
    audit_id: str = ""


@dataclass
class EvidenceNode:
    evidence_id: str
    evidence: EvidenceObject


@dataclass
class SupportEdge:
    claim_id: str
    evidence_id: str
    relation: str
    confidence: float = 0.5
