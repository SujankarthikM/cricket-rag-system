import json
import asyncio
from typing import Dict, List, Any
from config import Config
from services.llm_service import LLMService

class CricketQueryClassifier:
    def __init__(self):
        self.llm_service = LLMService()
        self.tools = Config.TOOLS
    
    async def classify_and_route(self, user_query: str) -> Dict[str, Any]:
        """
        Classify user query and determine which tools to use with specific instructions
        """
        
        # Build the classification prompt
        classification_prompt = self._build_classification_prompt(user_query)
        
        # Use LLM service for API call
        llm_response = await self.llm_service.classify_query(classification_prompt)
        
        if llm_response["success"]:
            result = llm_response["data"]
            # Validate and enhance the result
            enhanced_result = self._validate_and_enhance(result, user_query)
            # Add usage stats
            enhanced_result["llm_usage"] = llm_response.get("usage", {})
            return enhanced_result
        else:
            # Handle LLM service error
            return self._create_error_response(user_query, llm_response["error"])
    
    def _build_classification_prompt(self, query: str) -> str:
        """Build the classification prompt for LLM"""
        
        tools_description = "\n".join([
            f"{i+1}. {tool_key}: {tool_info['description']}"
            for i, (tool_key, tool_info) in enumerate(self.tools.items())
        ])
        
        prompt = f"""
Analyze this cricket query and determine which tools to use and suggest what you want to ask each tool:

Query: "{query}"

Available Tools:
{tools_description}

For each selected tool, provide specific instructions there can be two or more tools.So in the end you are acting like an tool selector and you are given these tools you have to pick what and which tools are you going to use and how too:

1. If opinion_rag is selected: Generate 5 diverse search queries for RAG system.Like the content in rag is just normal blogs writted by humans.Like it has debates,opinions articles and stuff.As queries keeping that in mind
2. If database_facts is selected: Specify what data needs to be fetched .Like in detail for example avg of kohli in test or all three formats.Like give what you want in detail
3. If live_data is selected: Specify what type of live data is needed in detail like match timing .Like whatever it is in detail.
4. If historical_match is selected: Specify date/tournament/team criteria Like you have to send the query in detail you get me such that it can be fetched form database
5. If visualization is selected: Specify chart type and data requirements.Like any kind of visualisations like comparision line/bar graph .Wagon wheel stuff like that.

Respond in this exact JSON format:
{{
    "tools_needed": ["tool1", "tool2"],
    "reasoning": "detailed explanation of why these tools were selected",
    "tool_instructions": {{
        "opinion_rag": {{
            "rag_queries": ["query1", "query2", "query3", "query4", "query5"],
            "analysis_focus": "what aspect to analyze"
        }},
        "database_facts": {{
            "sql_requirement": "what data to fetch",
            "specific_fields": ["field1", "field2"],
            "filters": "any specific conditions"
        }},
        "live_data": {{
            "data_type": "scores|commentary|weather|standings",
            "specific_matches": "any specific match criteria"
        }},
        "historical_match": {{
            "date_range": "specific dates or periods",
            "tournament": "tournament name if specified",
            "teams": ["team names if specified"]
        }},
        "visualization": {{
            "chart_type": "bar|line|pie|scatter|heatmap",
            "x_axis": "data for x-axis",
            "y_axis": "data for y-axis",
            "comparison_type": "what to compare"
        }}
    }},
    "confidence": 0.95,
    "query_type": "factual|opinion|live|historical|visual"
}}

Only include tool_instructions for the selected tools.
"""
        return prompt
    
    def _validate_and_enhance_agentic(self, llm_response: Dict, original_query: str) -> Dict[str, Any]:
        """Validate and enhance the agentic LLM response"""
        
        # Extract the key components from agentic response
        result = {
            "tools_needed": llm_response.get("tools_needed", ["opinion_rag"]),
            "reasoning": llm_response.get("reasoning", "Natural response provided"),
            "tool_instructions": llm_response.get("tool_instructions", {}),
            "query_type": llm_response.get("query_type", "general"),
            "confidence": llm_response.get("confidence", 0.7),
            
            # New agentic fields
            "natural_response": llm_response.get("natural_response", ""),
            "immediate_answer": llm_response.get("immediate_answer", ""),
            "enhancement_opportunities": llm_response.get("enhancement_opportunities", []),
            
            # Standard fields
            "original_query": original_query,
            "classification_success": True
        }
        
        # Add tool summaries for easy viewing
        result["tool_summaries"] = []
        for tool_name in result["tools_needed"]:
            if tool_name in self.tools:
                tool_info = self.tools[tool_name].copy()
                
                # Add specific instructions if available
                if tool_name in result["tool_instructions"]:
                    tool_info["instructions"] = result["tool_instructions"][tool_name]
                
                result["tool_summaries"].append({
                    "tool": tool_name,
                    "info": tool_info
                })
        
        return result
    
    def _validate_and_enhance(self, result: Dict, original_query: str) -> Dict[str, Any]:
        """Validate LLM response and add enhancements"""
        
        # Ensure required fields exist
        if "tools_needed" not in result:
            result["tools_needed"] = ["opinion_rag"]
        
        if "reasoning" not in result:
            result["reasoning"] = "Fallback classification"
        
        # Add metadata
        result["original_query"] = original_query
        result["classification_success"] = True
        
        # Add tool summaries for easy viewing
        result["tool_summaries"] = []
        for tool_name in result["tools_needed"]:
            if tool_name in self.tools:
                tool_info = self.tools[tool_name].copy()
                
                # Add specific instructions if available
                if "tool_instructions" in result and tool_name in result["tool_instructions"]:
                    tool_info["instructions"] = result["tool_instructions"][tool_name]
                
                result["tool_summaries"].append({
                    "tool": tool_name,
                    "info": tool_info
                })
        
        return result
    
    async def classify_multiple_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple queries in parallel"""
        tasks = [self.classify_and_route(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "original_query": queries[i],
                    "classification_success": False
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _create_error_response(self, user_query: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "error": error_message,
            "tools_needed": ["opinion_rag"],  # fallback
            "original_query": user_query,
            "reasoning": "Fallback due to classification error",
            "tool_instructions": {},
            "tool_summaries": [],
            "classification_success": False,
            "llm_usage": {}
        }