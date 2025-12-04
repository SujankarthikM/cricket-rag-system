import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Provider Settings
    LLM_PROVIDER = "gemini"
    GEMINI_API_KEY = "AIzaSyC7bAVtdapVd9HuyhCKk89KLwJhcg0c1IE"
    
    # Model Settings
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
