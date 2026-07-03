import os
import google.generativeai as genai
from .base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    def __init__(self, model: str = "gemini-1.5-flash"):
        api_key = os.environ.get("GEMINI_API_KEY", "")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def generate(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self._model.generate_content(full_prompt)
        return response.text
