from __future__ import annotations
import json
import re
from care.llm.base import BaseLLMClient
from care.jury.models import Claim

_SYSTEM = "You are a claim extraction engine. Extract structured claims from text."

_PROMPT = """Extract all verifiable claims from the following text as a JSON array.

Each claim must be a JSON object with these fields:
- text (string): the exact claim sentence
- claim_type (string): one of numeric_fact, factual, formula, generic, verb_style
- entity (string): main entity or subject
- metric (string): what is being measured or stated (empty string if not applicable)
- value (number or null): numeric value if present
- unit (string or null): unit of measurement if present
- time_period (string or null): time reference if present
- safety_sensitive (boolean): true if this claim could cause harm if wrong

Respond ONLY with a valid JSON array. No preamble, no markdown.

Text:
{text}"""


def _parse_json_array(raw: str) -> list[dict]:
    raw = raw.strip()
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def extract_claims(text: str, client: BaseLLMClient) -> list[Claim]:
    prompt = _PROMPT.format(text=text)
    raw = client.generate(prompt, system=_SYSTEM)
    items = _parse_json_array(raw)
    claims: list[Claim] = []
    for item in items:
        try:
            claims.append(
                Claim(
                    text=item.get("text", ""),
                    claim_type=item.get("claim_type", "generic"),
                    entity=item.get("entity", ""),
                    metric=item.get("metric", ""),
                    value=item.get("value"),
                    unit=item.get("unit"),
                    time_period=item.get("time_period"),
                    safety_sensitive=bool(item.get("safety_sensitive", False)),
                )
            )
        except Exception:
            continue
    return claims
