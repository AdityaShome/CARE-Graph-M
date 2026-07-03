from __future__ import annotations
import json
import re
from care.llm.base import BaseLLMClient
from care.jury.models import Claim, EvidenceObject

_SYSTEM = "You are a reasoning auditor. Evaluate whether a conclusion follows from the evidence."

_PROMPT = """Given the following claim and supporting evidence, rate how well the conclusion follows from the evidence.

Claim: {claim}
Evidence: {evidence}

Respond with JSON: {{"reasoning_score": <float 0.0-1.0>, "notes": "<brief explanation>"}}
Only output valid JSON.
"""


def audit_reasoning(
    claim: Claim,
    evidence: list[EvidenceObject],
    client: BaseLLMClient,
) -> float:
    if not evidence:
        return 0.3
    ev_text = " | ".join(e.content[:200] for e in evidence[:3])
    prompt = _PROMPT.format(claim=claim.text, evidence=ev_text)
    try:
        raw = client.generate(prompt, system=_SYSTEM)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return float(data.get("reasoning_score", 0.5))
    except Exception:
        pass
    return 0.5
