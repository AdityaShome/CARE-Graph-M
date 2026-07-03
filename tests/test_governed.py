import os
os.environ.setdefault("CARE_LLM_PROVIDER", "mock")

from care.service.governed import run_jury
from care.llm.mock import MockClient
from care.graph.store import get_store


def setup_function():
    get_store().clear()


def test_run_jury_returns_verdict():
    verdict = run_jury(
        question="What was revenue in Q3?",
        evidence_sources=[
            {
                "source_name": "Q3 Table",
                "source_type": "official_table",
                "table": [{"quarter": "Q3", "revenue": "8"}],
            }
        ],
        llm_client=MockClient(),
    )
    assert verdict.overall in ("APPROVED", "FLAGGED", "NEEDS_REVIEW", "BLOCKED", "UNRESOLVABLE")
    assert verdict.raw_answer != ""
    assert verdict.governed_answer != ""


def test_run_jury_stores_audit_id():
    verdict = run_jury(
        question="What is the capital of Germany?",
        evidence_sources=[{"source_name": "geo", "source_type": "official_documentation", "text": "Berlin is the capital of Germany."}],
        llm_client=MockClient(),
    )
    assert verdict.audit_id != ""


def test_fault_inject_still_produces_verdict():
    verdict = run_jury(
        question="What was revenue in Q3?",
        evidence_sources=[],
        fault_inject=True,
        llm_client=MockClient(),
    )
    assert verdict.overall in ("APPROVED", "FLAGGED", "NEEDS_REVIEW", "BLOCKED", "UNRESOLVABLE")
