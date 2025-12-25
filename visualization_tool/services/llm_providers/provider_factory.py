"""
LLM Provider Factory
"""
from .base_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider

def get_provider(name, **kwargs) -> BaseLLMProvider:
    if name == "gemini":
        return GeminiProvider(api_key=kwargs.get("api_key"))
    raise ValueError(f"Unsupported LLM provider: {name}")
