import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Provider Settings
    LLM_PROVIDER = "gemini"
    GEMINI_API_KEY = ""
    
    # PayPal CosmosAI Settings
    PAYPAL_API_URL = os.getenv("PAYPAL_API_URL", "https://aiplatform.dev51.cbf.dev.paypalinc.com/cosmosai/llm/v1/chat/completions")
    PAYPAL_API_TOKEN = os.getenv("PAYPAL_API_TOKEN", "e0947c6072ba8d6676bb2117dd903ce6db5eb8856731b162cddc2993cfba99a5")
    
    # OpenAI Settings (backup)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Settings
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    # Tool definitions
    TOOLS = {
        "opinion_rag": {
            "name": "Opinion Analysis Tool",
            "description": "For subjective analysis, comparisons, explanations, 'why' questions",
            "purpose": "Generate 5 search queries for RAG system"
        },
        "database_facts": {
            "name": "Database Facts Tool", 
            "description": "For direct factual data like runs, averages, records, 'who has more'",
            "purpose": "Convert to SQL query requirement"
        },
        "live_data": {
            "name": "Live Data Tool",
            "description": "For current/ongoing matches, today's games, live scores",
            "purpose": "Fetch real-time cricket data"
        },
        "historical_match": {
            "name": "Historical Match Tool",
            "description": "For specific past matches, tournaments, dates",
            "purpose": "Find specific match records"
        },
        "visualization": {
            "name": "Visualization Tool",
            "description": "For queries asking for charts, graphs, trends, visual data",
            "purpose": "Generate charts and graphs"
        }
    }