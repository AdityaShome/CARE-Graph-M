"""End-to-end demo using MockClient — no API key required."""
import os
os.environ["CARE_LLM_PROVIDER"] = "mock"

from care.service.governed import run_jury
from care.llm.mock import MockClient

EVIDENCE = [
    {
        "source_name": "Q3 Official Revenue Table",
        "source_type": "official_table",
        "table": [{"quarter": "Q3", "revenue": "8"}],
    }
]

print("=" * 60)
print("CARE-Graph-M — Demo")
print("=" * 60)

verdict = run_jury(
    question="What was revenue in Q3?",
    evidence_sources=EVIDENCE,
    fault_inject=True,
    llm_client=MockClient(),
)

print(f"\nRaw answer:      {verdict.raw_answer}")
print(f"Governed answer: {verdict.governed_answer}")
print(f"Verdict:         {verdict.overall}")
print(f"Confidence:      {verdict.confidence_scalar:.2f}")
print(f"Audit ID:        {verdict.audit_id}")
print()
for cv in verdict.claim_verdicts:
    print(f"  Claim: {cv.claim.text}")
    print(f"  Relation: {cv.relation}")
    if cv.correction:
        print(f"  Correction: {cv.correction}")
    print()
