from .base import BaseLLMClient

_CLAIM_TEMPLATE = """[
  {
    "text": "Revenue was 10 in Q3.",
    "claim_type": "numeric_fact",
    "entity": "revenue",
    "metric": "revenue",
    "value": 10,
    "unit": null,
    "time_period": "Q3",
    "safety_sensitive": false
  }
]"""

_ANSWER_TEMPLATE = "Revenue was 10 in Q3. This is a mock answer."

_CORRECTION_TEMPLATE = "Revenue was 8 in Q3."

_REASONING_TEMPLATE = '{"reasoning_score": 0.8, "notes": "Conclusion follows from evidence."}'


class MockClient(BaseLLMClient):
    def generate(self, prompt: str, system: str = "") -> str:
        low = prompt.lower()
        if "extract" in low and "claim" in low:
            return _CLAIM_TEMPLATE
        if "rewrite" in low or "correction" in low or "correct" in low:
            return _CORRECTION_TEMPLATE
        if "reasoning" in low or "auditor" in low or "audit" in low:
            return _REASONING_TEMPLATE
        return _ANSWER_TEMPLATE
