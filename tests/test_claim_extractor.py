from care.jury.claim_extractor import extract_claims
from care.llm.mock import MockClient


def test_extract_basic():
    client = MockClient()
    claims = extract_claims("Revenue was 10 in Q3.", client)
    assert len(claims) >= 1
    c = claims[0]
    assert c.text != ""
    assert c.claim_type in ("numeric_fact", "factual", "formula", "generic", "verb_style")


def test_extract_numeric_claim():
    client = MockClient()
    claims = extract_claims("Revenue was 10 in Q3.", client)
    numeric = [c for c in claims if c.value is not None]
    assert len(numeric) >= 1
    assert numeric[0].value == 10
