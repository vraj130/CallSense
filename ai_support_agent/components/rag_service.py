import json
import aiofiles
from typing import Dict, List
from config import Config
from components.llm_service import LLMService

class RAGService:
    def __init__(self):
        self.knowledge_base = {}
        self.policies = ""
        self.llm_service = LLMService()
    
    async def initialize(self):
        """Load knowledge base and policies"""
        try:
            # Load knowledge base
            async with aiofiles.open(Config.KNOWLEDGE_BASE_PATH, 'r') as f:
                content = await f.read()
                self.knowledge_base = json.loads(content)
            
            # Load policies
            async with aiofiles.open(Config.POLICIES_PATH, 'r') as f:
                self.policies = await f.read()
            # print("[RAGService] Loaded knowledge base:", self.knowledge_base)
            
            # print("[RAGService] Loading policies from:", Config.POLICIES_PATH)

        except Exception as e:
            print(f"Error loading data: {e}")
            # Use default data for MVP
            self.knowledge_base = {
                "order_status": {
                    "ORDER-12345": "Shipped - Expected delivery: 2 days",
                    "ORDER-67890": "Processing - Expected ship date: Tomorrow"
                },
                "return_policy": "Items can be returned within 30 days of purchase",
                "shipping_info": "Standard shipping: 5-7 days, Express: 2-3 days"
            }
            self.policies = "Company policies: Customer satisfaction is our priority."
    
    async def search(self, query: str) -> str:
        """Context-based LLM response using all knowledge base and policies as context."""
        # Flatten knowledge base and policies into a context string
        context = "Knowledge Base and Policies:\n"
        for key, value in self.knowledge_base.items():
            if isinstance(value, dict):
                context += f"{key}:\n"
                for subkey, subval in value.items():
                    context += f"  {subkey}: {subval}\n"
            else:
                context += f"{key}: {value}\n"
        context += f"\nPolicies:\n{self.policies}\n"
        prompt = f"""
You are a helpful assistant. Use the following context to answer the user's question.

Context:
{context}

Question: {query}

Answer as helpfully and concisely as possible based only on the provided context.
"""
        print(f"[RAGService] Sending prompt to LLM:\n{prompt}")
        # Use the LLMService to get a response
        response = await self.llm_service._call_openai(prompt)
        # If the LLM returns a dict, get the content; otherwise, return as is
        if isinstance(response, dict) and "answer" in response:
            return response["answer"]
        elif isinstance(response, str):
            return response
        else:
            return str(response) 