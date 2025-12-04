"""
LLM Service - All LLM API interactions happen here
Supports multiple providers (PayPal CosmosAI, OpenAI, etc.)
"""
import json
from typing import Dict, Any, List
from ..config import Config
from .llm_providers.provider_factory import get_provider
from .llm_providers.base_provider import BaseLLMProvider

class LLMService:
    def __init__(self):
        if Config.LLM_PROVIDER == "gemini":
            self.provider = get_provider("gemini", api_key=Config.GEMINI_API_KEY)
        # ...existing code for other providers...

    async def classify_query(self, classification_prompt: str) -> Dict[str, Any]:
        """
        Make API call to LLM for query classification
        
        Args:
            classification_prompt: The prompt for classification (from query_classifier.py)
            
        Returns:
            Dict containing classification results or error
        """
        # Simple system prompt - let the classification_prompt do the work
        system_prompt = "You are a cricket query classifier. Respond only in valid JSON format."
        
        messages = self.provider.format_messages(system_prompt, classification_prompt)
        
        # Make the API call using the configured provider
        response = await self.provider.chat_completion(messages, max_tokens=1000)
        
        if not response["success"]:
            return response
        
        # Try to parse the JSON response
        try:
            content = response["content"].strip()
            # Try to extract JSON if there's extra text
            if not content.startswith('{'):
                # Look for JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx:end_idx+1]
            
            result = json.loads(content)
            return {
                "success": True,
                "data": result,
                "usage": response.get("usage", {}),
                "provider": self.provider.get_provider_name()
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse LLM response as JSON: {str(e)}",
                "error_type": "json_parse_error",
                "raw_content": response["content"]
            }
    
    def generate_fallback_rag_queries(self, original_query: str) -> List[str]:
        """Generate fallback RAG queries based on keywords"""
        query_lower = original_query.lower()
        
        # Extract player names and key terms
        players = []
        key_terms = []
        
        # Common cricket player names
        common_players = ["kohli", "rohit", "dhoni", "sachin", "bumrah", "ashwin", "pant", "rahul"]
        for player in common_players:
            if player in query_lower:
                players.append(player.title())
        
        # Key cricket terms
        if any(word in query_lower for word in ["best", "top", "greatest"]):
            key_terms.append("best")
        if any(word in query_lower for word in ["innings", "knock", "performance"]):
            key_terms.append("innings")
        if any(word in query_lower for word in ["century", "hundred"]):
            key_terms.append("century")
        if any(word in query_lower for word in ["captain", "leadership"]):
            key_terms.append("captaincy")
        if any(word in query_lower for word in ["compare", "vs", "versus"]):
            key_terms.append("comparison")
        
        # Generate fallback queries
        fallback_queries = []
        
        if players and key_terms:
            player = players[0]
            if "best" in key_terms and "innings" in key_terms:
                fallback_queries = [
                    f"Top {player} innings",
                    f"Best {player} knocks", 
                    f"{player} greatest performances",
                    f"{player} memorable batting",
                    f"{player} highest scores analysis"
                ]
            elif "captaincy" in key_terms:
                fallback_queries = [
                    f"{player} captaincy style",
                    f"{player} leadership analysis",
                    f"{player} captain performance",
                    f"{player} tactical decisions",
                    f"{player} team management"
                ]
            elif "comparison" in key_terms:
                fallback_queries = [
                    f"{player} vs other players",
                    f"{player} comparison analysis",
                    f"{player} performance debate",
                    f"{player} ranking discussion",
                    f"{player} career evaluation"
                ]
        
        if not fallback_queries:
            # Generic cricket content queries
            fallback_queries = [
                "cricket player analysis",
                "cricket performance debate",
                "cricket expert opinion",
                "cricket match discussion",
                "cricket batting analysis"
            ]
        
        return fallback_queries[:5]
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the current LLM provider and model"""
        if hasattr(self.provider, 'get_config_info'):
            return self.provider.get_config_info()
        else:
            return {
                "provider": self.provider.get_provider_name(),
                "model": getattr(self.provider, 'model', 'unknown')
            }
    
    def get_provider(self) -> BaseLLMProvider:
        """Get the current provider instance"""
        return self.provider
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the LLM provider connection"""
        system_prompt = "You are a helpful assistant. Respond only with valid JSON format."
        user_prompt = """Respond with exactly this JSON format:
{
    "message": "Hello, I am working!",
    "status": "connected"
}

JSON Response:"""
        
        test_messages = self.provider.format_messages(system_prompt, user_prompt)
        
        response = await self.provider.chat_completion(test_messages, max_tokens=100)
        
        if response["success"]:
            try:
                # Try to parse as JSON
                content = response["content"].strip()
                if not content.startswith('{'):
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        content = content[start_idx:end_idx+1]
                
                parsed_json = json.loads(content)
                return {
                    "success": True,
                    "message": "LLM provider connection successful",
                    "provider": self.provider.get_provider_name(),
                    "test_response": parsed_json,
                    "usage": response.get("usage", {})
                }
            except json.JSONDecodeError:
                # Connection works but JSON parsing failed
                return {
                    "success": True,
                    "message": "LLM provider connection successful (but JSON parsing needs work)",
                    "provider": self.provider.get_provider_name(),
                    "raw_response": response["content"][:200],
                    "warning": "Provider returns text instead of JSON format"
                }
        else:
            return {
                "success": False,
                "message": "LLM provider connection failed",
                "error": response["error"]
            }