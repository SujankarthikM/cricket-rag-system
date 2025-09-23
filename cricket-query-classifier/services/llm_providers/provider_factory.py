"""
LLM Provider Factory - Creates the appropriate provider based on configuration
"""
from typing import Union
from config import Config
from .paypal_provider import PayPalProvider
from .base_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider

class LLMProviderFactory:
    """Factory to create LLM providers based on configuration"""
    
    @staticmethod
    def create_provider() -> BaseLLMProvider:
        """Create and return the configured LLM provider"""
        
        provider_type = Config.LLM_PROVIDER.lower()
        
        if provider_type == "paypal":
            return PayPalProvider(
                api_url=Config.PAYPAL_API_URL,
                api_token=Config.PAYPAL_API_TOKEN,
                model=Config.LLM_MODEL,
                max_tokens=Config.LLM_MAX_TOKENS,
                temperature=Config.LLM_TEMPERATURE
            )
        
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_type}")
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available providers"""
        return ["paypal"]
    
    @staticmethod
    def get_provider_info(provider_type: str) -> dict:
        """Get information about a specific provider"""
        provider_info = {
            "paypal": {
                "name": "PayPal CosmosAI",
                "description": "PayPal's internal LLM platform",
                "required_config": ["PAYPAL_API_URL", "PAYPAL_API_TOKEN"]
            }
        }
        
        return provider_info.get(provider_type.lower(), {})

def get_provider(name, **kwargs):
    if name == "gemini":
        return GeminiProvider(api_key=kwargs.get("api_key"))