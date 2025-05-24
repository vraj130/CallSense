## config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()




class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


    LLM_SYSTEM_PROMPT_PATH = os.getenv("LLM_SYSTEM_PROMPT_PATH", "data/system_prompt.txt")

    LLM_MODEL = "gpt-4o"
    KNOWLEDGE_BASE_PATH = "data/knowledge_base.json"
    POLICIES_PATH = "data/policies.txt"
    GRADIO_PORT = 7860

    # Server Configuration
    SERVER_HOST = "localhost"
    SERVER_PORT = 7866
    # Browser Configuration
    BROWSER_HEADLESS = False  # Set to False to see the browser in action
    BROWSER_TIMEOUT = 30000  # 30 seconds
    BROWSER_WINDOW_SIZE = (1280, 800)  # Width, Height