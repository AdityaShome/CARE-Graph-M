from care.jury.models import Claim, EvidenceObject
from care.jury.fact_verifier import verify_claim, _numeric_delta


def _ev(content, numeric_value=None, source_type="official_table", reliability=0.9):
    return EvidenceObject(
        source_id="test",
        source_type=source_type,
        content=content,
        reliability_score=reliability,
        numeric_value=numeric_value,
    )


def test_numeric_delta_exact():
    assert _numeric_delta(10, 10) == 0.0


def test_numeric_delta_small():
    assert _numeric_delta(10, 10.05) < 0.01


def test_supported_numeric():
    claim = Claim(text="Revenue was 8 in Q3.", claim_type="numeric_fact", value=8.0)
    ev = [_ev("Q3 revenue=8", numeric_value=8.0)]
    cv = verify_claim(claim, ev)
    assert cv.relation == "supported"


def test_contradicted_numeric():
    claim = Claim(text="Revenue was 10 in Q3.", claim_type="numeric_fact", value=10.0)
    ev = [_ev("Q3 revenue=8", numeric_value=8.0)]
    cv = verify_claim(claim, ev)
    assert cv.relation == "contradicted"


def test_unsupported_no_evidence():
    claim = Claim(text="Revenue was 10.", claim_type="numeric_fact", value=10.0)
    cv = verify_claim(claim, [])
    assert cv.relation in ("unsupported", "needs_review")


def test_text_claim_supported():
    claim = Claim(text="Berlin is the capital of Germany.", claim_type="factual")
    ev = [_ev("Berlin is the capital of Germany and a major European city.")]
    cv = verify_claim(claim, ev)
    assert cv.relation in ("supported", "partially_supported")
