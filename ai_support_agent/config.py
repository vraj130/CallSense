## config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    LLM_SYSTEM_PROMPT_PATH = os.getenv("LLM_SYSTEM_PROMPT_PATH", "data/system_prompt.txt")

    LLM_MODEL = "gpt-4o"
    KNOWLEDGE_BASE_PATH = "data/knowledge_base.json"
    POLICIES_PATH = "data/policies.txt"
    GRADIO_PORT = 7860