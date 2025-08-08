"""
OpenAI LLM Provider (backup option)
"""
from typing import Dict, Any, List
from openai import AsyncOpenAI
from .base_provider import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider as backup option"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", 
                 max_tokens: int = 1000, temperature: float = 0.1):
        super().__init__(model, max_tokens, temperature)
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Make chat completion request to OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature)
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}",
                "error_type": "api_error"
            }
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "OpenAI"