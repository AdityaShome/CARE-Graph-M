from __future__ import annotations
from care.llm.base import BaseLLMClient
from care.jury.models import ClaimVerdict

_SYSTEM = "You are a precise correction agent. Rewrite claims using only the provided evidence."

_PROMPT = """The following claim is contradicted by evidence. Rewrite ONLY the contradicted claim using the provided evidence. Do not add information not in the evidence.

Original claim: {claim}
Evidence: {evidence}

Output the corrected sentence only. No explanation.
"""


def correct_claim(cv: ClaimVerdict, client: BaseLLMClient) -> str:
    if cv.relation != "contradicted" or not cv.evidence_used:
        return cv.claim.text
    ev_text = " | ".join(e.content[:300] for e in cv.evidence_used[:2])
    prompt = _PROMPT.format(claim=cv.claim.text, evidence=ev_text)
    corrected = client.generate(prompt, system=_SYSTEM).strip()
    return corrected if corrected else cv.claim.text


def apply_corrections(
    raw_answer: str,
    claim_verdicts: list[ClaimVerdict],
    client: BaseLLMClient,
) -> str:
    answer = raw_answer
    for cv in claim_verdicts:
        if cv.relation == "contradicted":
            correction = correct_claim(cv, client)
            cv.correction = correction
            answer = answer.replace(cv.claim.text, correction)
    return answer
