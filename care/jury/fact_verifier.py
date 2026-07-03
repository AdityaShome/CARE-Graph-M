from __future__ import annotations
import re
from care.jury.models import Claim, ClaimVerdict, EvidenceObject, Relation


_NOISE = 0.01
_SOFT = 0.20


def _numeric_delta(claim_val: float, ev_val: float) -> float:
    return abs(claim_val - ev_val) / max(abs(ev_val), 1e-9)


def _extract_number(text: str) -> float | None:
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)
    if matches:
        return float(matches[0])
    return None


def _keyword_overlap(a: str, b: str) -> float:
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def verify_claim(
    claim: Claim,
    evidence: list[EvidenceObject],
) -> ClaimVerdict:
    if not evidence:
        relation: Relation = "needs_review" if claim.safety_sensitive else "unsupported"
        return ClaimVerdict(claim=claim, relation=relation, evidence_used=[])

    if claim.value is not None:
        # Numeric claim path
        best_ev: EvidenceObject | None = None
        best_delta = float("inf")
        for ev in evidence:
            ev_val = ev.numeric_value
            if ev_val is None:
                ev_val = _extract_number(ev.content)
            if ev_val is None:
                continue
            d = _numeric_delta(claim.value, ev_val)
            if d < best_delta:
                best_delta = d
                best_ev = ev

        if best_ev is None:
            return ClaimVerdict(
                claim=claim,
                relation="unsupported",
                evidence_used=evidence,
            )

        if best_delta < _NOISE:
            relation = "supported"
        elif best_delta < _SOFT:
            relation = "partially_supported"
        else:
            relation = "contradicted"

        return ClaimVerdict(
            claim=claim,
            relation=relation,
            evidence_used=[best_ev],
            math_validity=max(0.0, 1.0 - best_delta),
        )

    # Text / generic claim path
    best_ev = max(evidence, key=lambda e: _keyword_overlap(claim.text, e.content))
    overlap = _keyword_overlap(claim.text, best_ev.content)

    if overlap >= 0.4:
        relation = "supported"
    elif overlap >= 0.15:
        relation = "partially_supported"
    elif overlap > 0:
        relation = "ambiguous"
    else:
        relation = "unsupported"

    return ClaimVerdict(
        claim=claim,
        relation=relation,
        evidence_used=[best_ev],
        math_validity=0.5,
        reasoning_score=overlap,
    )
