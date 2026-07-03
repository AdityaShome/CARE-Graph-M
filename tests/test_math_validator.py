from care.jury.models import Claim
from care.jury.math_validator import validate_math


def test_exact_match():
    claim = Claim(text="Revenue is 8.", claim_type="numeric_fact", value=8.0, unit="usd")
    score = validate_math(claim, ev_value=8.0, ev_unit="usd")
    assert score == 1.0


def test_near_match():
    claim = Claim(text="Revenue is 8.", claim_type="numeric_fact", value=8.0)
    score = validate_math(claim, ev_value=8.1, ev_unit=None)
    assert score > 0.9


def test_mismatch():
    claim = Claim(text="Revenue is 10.", claim_type="numeric_fact", value=10.0)
    score = validate_math(claim, ev_value=8.0, ev_unit=None)
    assert score < 0.8


def test_unit_conflict():
    claim = Claim(text="Distance is 10 km.", claim_type="numeric_fact", value=10.0, unit="km")
    score = validate_math(claim, ev_value=10.0, ev_unit="kg")
    assert score == 0.1


def test_no_claim_value():
    claim = Claim(text="Some text.", claim_type="generic")
    score = validate_math(claim, ev_value=5.0, ev_unit=None)
    assert score == 0.5
