## config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Model settings
    LLM_MODEL = "gpt-3.5-turbo"
    
    # File paths
    KNOWLEDGE_BASE_PATH = "data/knowledge_base.json"
    POLICIES_PATH = "data/policies.txt"
    
    # Server settings
    GRADIO_PORT = 7860