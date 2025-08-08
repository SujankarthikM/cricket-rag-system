"""
PayPal CosmosAI LLM Provider
"""
import aiohttp
import json
from typing import Dict, Any, List
from .base_provider import BaseLLMProvider

class PayPalProvider(BaseLLMProvider):
    """PayPal CosmosAI LLM Provider using your curl endpoint"""
    
    def __init__(self, api_url: str, api_token: str, model: str = "gpt-4o-mini", 
                 max_tokens: int = 1000, temperature: float = 0.1):
        super().__init__(model, max_tokens, temperature)
        self.api_url = api_url
        self.api_token = api_token
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Make chat completion request to PayPal CosmosAI
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "messages": messages
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, 
                    headers=headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_success_response(data)
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "error_type": "http_error"
                        }
        
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "error_type": "network_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error"
            }
    
    def _parse_success_response(self, data: Dict) -> Dict[str, Any]:
        """Parse successful response from PayPal CosmosAI"""
        try:
            # Assuming response format similar to OpenAI
            content = data["choices"][0]["message"]["content"]
            
            usage = {}
            if "usage" in data:
                usage = {
                    "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                    "completion_tokens": data["usage"].get("completion_tokens", 0),
                    "total_tokens": data["usage"].get("total_tokens", 0)
                }
            
            return {
                "success": True,
                "content": content,
                "usage": usage,
                "raw_response": data
            }
            
        except (KeyError, IndexError) as e:
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "error_type": "parse_error",
                "raw_response": data
            }
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "PayPal CosmosAI"
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        return {
            "provider": self.get_provider_name(),
            "model": self.model,
            "api_url": self.api_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }