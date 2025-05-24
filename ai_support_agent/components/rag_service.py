import json
import aiofiles
from typing import Dict, List
from config import Config

class RAGService:
    def __init__(self):
        self.knowledge_base = {}
        self.policies = ""
    
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
        """Simple keyword-based search"""
        query_lower = query.lower()
        results = []
        
        # Search in knowledge base
        for key, value in self.knowledge_base.items():
            if any(keyword in query_lower for keyword in key.lower().split('_')):
                if isinstance(value, dict):
                    # Check for specific order numbers
                    for order_id, status in value.items():
                        if order_id in query:
                            results.append(f"{order_id}: {status}")
                else:
                    results.append(f"{key}: {value}")
        
        # Search in policies
        if "policy" in query_lower or "return" in query_lower:
            results.append(f"Policy Information: {self.policies[:200]}...")
        
        if results:
            return "\n".join(results)
        else:
            return "No relevant information found. Please provide more details." 