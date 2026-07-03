from __future__ import annotations
import os
from care.llm.factory import get_llm_client
from care.llm.base import BaseLLMClient
from care.jury.claim_extractor import extract_claims
from care.jury.evidence_parser import parse_evidence
from care.jury.fact_verifier import verify_claim
from care.jury.math_validator import validate_math
from care.jury.reasoning_auditor import audit_reasoning
from care.jury.verdict_engine import decide_verdict
from care.jury.correction_agent import apply_corrections
from care.jury.scoring import build_confidence_vector
from care.jury.audit_logger import log_verdict
from care.jury.models import ClaimVerdict, JuryVerdict
from care.graph.store import get_store
from care.retrieval.hybrid import retrieve

_FAULT_PROMPT = (
    "You are an AI that confidently answers questions but sometimes makes subtle "
    "numerical errors in dates, values, and statistics. Answer the question below."
)
_NORMAL_PROMPT = "Answer the following question accurately and concisely."


def run_jury(
    question: str,
    evidence_sources: list[dict] | None = None,
    use_graph_context: bool = False,
    fault_inject: bool = False,
    llm_client: BaseLLMClient | None = None,
) -> JuryVerdict:
    client = llm_client or get_llm_client()
    fault = fault_inject or os.environ.get("CARE_FAULT_INJECT", "false").lower() == "true"

    # Agent 1: Generate raw answer
    system = _FAULT_PROMPT if fault else _NORMAL_PROMPT
    raw_answer = client.generate(question, system=system)

    # Parse inline evidence
    inline_ev = parse_evidence(evidence_sources or [])

    # Optionally retrieve from global store
    store = get_store()
    if use_graph_context or not inline_ev:
        store_ev = retrieve(question, store, top_k=5)
        all_evidence = inline_ev + store_ev
    else:
        all_evidence = inline_ev

    # Agent 2: Extract claims
    claims = extract_claims(raw_answer, client)
    if not claims:
        # Fallback: treat whole answer as one generic claim
        from care.jury.models import Claim
        claims = [Claim(text=raw_answer[:500], claim_type="generic")]

    # Agents 3, 4, 5: Verify each claim
    claim_verdicts: list[ClaimVerdict] = []
    for claim in claims:
        relevant_ev = [
            e for e in all_evidence
            if (claim.entity and claim.entity.lower() in e.content.lower())
            or (claim.metric and claim.metric.lower() in e.content.lower())
        ] or all_evidence

        cv = verify_claim(claim, relevant_ev)

        # Math validator signal
        ev_val = relevant_ev[0].numeric_value if relevant_ev else None
        ev_unit = relevant_ev[0].metadata.get("unit") if relevant_ev else None
        cv.math_validity = validate_math(claim, ev_val, ev_unit)

        # Reasoning auditor signal
        cv.reasoning_score = audit_reasoning(claim, cv.evidence_used, client)

        # Build confidence vector
        cv.confidence = build_confidence_vector(cv, cv.evidence_used)
        claim_verdicts.append(cv)

    # Verdict engine
    overall = decide_verdict(claim_verdicts)

    # Correction agent
    governed_answer = raw_answer
    if overall == "FLAGGED":
        governed_answer = apply_corrections(raw_answer, claim_verdicts, client)

    # Confidence scalar
    if claim_verdicts:
        confidence_scalar = sum(cv.confidence.scalar() for cv in claim_verdicts) / len(claim_verdicts)
    else:
        confidence_scalar = 0.5

    verdict = JuryVerdict(
        overall=overall,
        claim_verdicts=claim_verdicts,
        raw_answer=raw_answer,
        governed_answer=governed_answer,
        confidence_scalar=confidence_scalar,
    )

    log_verdict(question, verdict)
    return verdict
