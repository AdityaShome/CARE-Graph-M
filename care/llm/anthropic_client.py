import os
import anthropic
from .base import BaseLLMClient


class AnthropicClient(BaseLLMClient):
    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        self._model = model

    def generate(self, prompt: str, system: str = "") -> str:
        kwargs: dict = {"model": self._model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
        if system:
            kwargs["system"] = system
        message = self._client.messages.create(**kwargs)
        return message.content[0].text
