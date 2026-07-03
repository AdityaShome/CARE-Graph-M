import os
from .base import BaseLLMClient


def get_llm_client(provider: str | None = None) -> BaseLLMClient:
    provider = provider or os.environ.get("CARE_LLM_PROVIDER", "mock")
    if provider == "gemini":
        from .gemini import GeminiClient
        return GeminiClient()
    if provider == "groq":
        from .groq_client import GroqClient
        return GroqClient()
    if provider == "anthropic":
        from .anthropic_client import AnthropicClient
        return AnthropicClient()
    from .mock import MockClient
    return MockClient()
