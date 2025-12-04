from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
from query_classifier import CricketQueryClassifier

app = FastAPI(
    title="Cricket Query Classifier",
    description="Classify cricket queries and route to appropriate tools",
    version="1.0.0"
)

classifier = CricketQueryClassifier()

class QueryRequest(BaseModel):
    query: str

class MultiQueryRequest(BaseModel):
    queries: List[str]

class ClassificationResponse(BaseModel):
    tools_needed: List[str]
    reasoning: str = "Classification completed"
    tool_instructions: Dict[str, Any] = {}
    original_query: str
    tool_summaries: List[Dict[str, Any]] = []
    confidence: float = None
    query_type: str = None
    error: str = None
    llm_usage: Dict[str, Any] = {}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Cricket Query Classifier API",
        "version": "1.0.0",
        "endpoints": {
            "classify": "POST /classify - Classify a single query",
            "classify-batch": "POST /classify-batch - Classify multiple queries",
            "tools": "GET /tools - List available tools",
            "examples": "GET /examples - See example classifications"
        }
    }

@app.post("/classify", response_model=ClassificationResponse)
async def classify_query(request: QueryRequest):
    """
    Classify a cricket query and determine which tools to use
    
    Returns detailed classification with specific instructions for each tool
    """
    try:
        result = await classifier.classify_and_route(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.post("/classify-batch")
async def classify_multiple_queries(request: MultiQueryRequest):
    """
    Classify multiple cricket queries in parallel
    """
    try:
        results = await classifier.classify_multiple_queries(request.queries)
        return {
            "total_queries": len(request.queries),
            "results": results,
            "summary": {
                "successful": sum(1 for r in results if r.get("classification_success", False)),
                "failed": sum(1 for r in results if not r.get("classification_success", False))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch classification failed: {str(e)}")

@app.get("/tools")
async def get_available_tools():
    """List all available tools and their descriptions"""
    from config import Config
    return {
        "tools": Config.TOOLS,
        "total_tools": len(Config.TOOLS)
    }

@app.get("/llm/info")
async def get_llm_info():
    """Get information about the current LLM provider"""
    try:
        model_info = classifier.llm_service.get_model_info()
        return {
            "llm_provider": model_info,
            "status": "configured"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get LLM info: {str(e)}")

@app.post("/llm/test")
async def test_llm_connection():
    """Test the LLM provider connection"""
    try:
        result = await classifier.llm_service.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM test failed: {str(e)}")

@app.get("/examples")
async def get_example_classifications():
    """
    Show example queries and their expected classifications
    """
    examples = [
        {
            "query": "Who has more runs Kohli or Rohit?",
            "expected_tools": ["database_facts"],
            "expected_type": "factual"
        },
        {
            "query": "Why is Kohli better than Rohit?",
            "expected_tools": ["opinion_rag"],
            "expected_type": "opinion"
        },
        {
            "query": "What's the current score in India vs Australia?",
            "expected_tools": ["live_data"],
            "expected_type": "live"
        },
        {
            "query": "Show me Kohli's run trend over the last 3 years",
            "expected_tools": ["database_facts", "visualization"],
            "expected_type": "visual"
        },
        {
            "query": "Tell me about the 2019 World Cup final",
            "expected_tools": ["historical_match", "opinion_rag"],
            "expected_type": "historical"
        }
    ]
    
    return {
        "examples": examples,
        "note": "Use POST /classify to test these queries"
    }

@app.post("/demo")
async def demo_classification():
    """
    Demo endpoint that shows classification for multiple example queries
    """
    demo_queries = [
        "Who has more runs Kohli or Rohit?",
        "Why is Kohli better than Rohit?", 
        "What's the current score in India vs Australia?",
        "Show me Kohli's performance trend",
        "Tell me about the 2019 World Cup final",
        "Compare Bumrah and Shami bowling figures",
        "What happened in today's match?",
        "Who won the most IPL titles?",
        "Can you tell me sachins best matches?"
    ]
    
    try:
        results = await classifier.classify_multiple_queries(demo_queries)
        
        # Format results for easy viewing
        formatted_results = []
        for result in results:
            formatted_results.append({
                "query": result["original_query"],
                "tools": result["tools_needed"],
                "reasoning": result["reasoning"],
                "instructions_summary": {
                    tool: list(instructions.keys()) 
                    for tool, instructions in result.get("tool_instructions", {}).items()
                }
            })
        
        return {
            "demo_results": formatted_results,
            "total_queries": len(demo_queries),
            "note": "This shows how different queries get routed to different tools"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🏏 Starting Cricket Query Classifier API...")
    print("📡 API will be available at: http://localhost:8000")
    print("📖 Interactive docs at: http://localhost:8000/docs")
    print("🎯 Demo endpoint: http://localhost:8000/demo")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)