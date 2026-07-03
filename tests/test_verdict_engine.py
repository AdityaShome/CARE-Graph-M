from care.jury.models import Claim, ClaimVerdict, EvidenceObject, ConfidenceVector
from care.jury.verdict_engine import decide_verdict


def _cv(relation, safety=False, reliability=0.9):
    ev = EvidenceObject(source_id="s", source_type="official_table", content="x", reliability_score=reliability)
    return ClaimVerdict(
        claim=Claim(text="test", claim_type="numeric_fact", safety_sensitive=safety),
        relation=relation,
        evidence_used=[ev],
        confidence=ConfidenceVector(),
    )


def test_all_supported():
    assert decide_verdict([_cv("supported"), _cv("supported")]) == "APPROVED"


def test_contradicted_high_reliability():
    assert decide_verdict([_cv("contradicted", reliability=0.9)]) == "FLAGGED"


def test_safety_unsupported():
    assert decide_verdict([_cv("unsupported", safety=True)]) == "NEEDS_REVIEW"


def test_blocked():
    assert decide_verdict([_cv("blocked")]) == "BLOCKED"


def test_unresolvable():
    assert decide_verdict([_cv("unresolvable")]) == "UNRESOLVABLE"


def test_empty():
    assert decide_verdict([]) == "NEEDS_REVIEW"


def test_partial_needs_review():
    assert decide_verdict([_cv("supported"), _cv("partially_supported")]) == "NEEDS_REVIEW"
