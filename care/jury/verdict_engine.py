from __future__ import annotations
from care.jury.models import ClaimVerdict, OverallVerdict


def decide_verdict(claim_verdicts: list[ClaimVerdict]) -> OverallVerdict:
    if not claim_verdicts:
        return "NEEDS_REVIEW"

    relations = [cv.relation for cv in claim_verdicts]

    if any(r == "blocked" for r in relations):
        return "BLOCKED"

    if any(r == "unresolvable" for r in relations):
        return "UNRESOLVABLE"

    # Safety-sensitive claims with no evidence
    safety_unsupported = any(
        cv.claim.safety_sensitive and cv.relation in ("unsupported", "needs_review")
        for cv in claim_verdicts
    )
    if safety_unsupported:
        return "NEEDS_REVIEW"

    # Hard contradiction with high-reliability evidence
    hard_contradictions = [
        cv for cv in claim_verdicts
        if cv.relation == "contradicted"
        and any(e.reliability_score >= 0.7 for e in cv.evidence_used)
    ]
    if hard_contradictions:
        return "FLAGGED"

    # Soft contradictions or missing evidence
    if any(r in ("partially_supported", "ambiguous", "unsupported", "needs_review") for r in relations):
        return "NEEDS_REVIEW"

    return "APPROVED"
