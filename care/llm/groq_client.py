import os
from groq import Groq
from .base import BaseLLMClient


class GroqClient(BaseLLMClient):
    def __init__(self, model: str = "llama3-8b-8192"):
        self._client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        self._model = model

    def generate(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""
