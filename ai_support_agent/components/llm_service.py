import openai
from typing import List
import json
from config import Config
from utils.models import TranscriptEntry, Task
import uuid

class LLMService:
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
    
    async def generate_task_from_transcript(self, transcript: List[TranscriptEntry]) -> Task:
        """Generate task/plan from conversation transcript"""
        
        # Format transcript for LLM
        conversation = "\n".join([
            f"{entry.speaker.value}: {entry.text}" 
            for entry in transcript
        ])
        
        prompt = f"""
        Analyze this customer support conversation and generate a task to help the agent:
        
        {conversation}
        
        Return a JSON with:
        - task_description: What needs to be done
        - plan: Step-by-step plan to resolve the issue
        - task_type: "rag" (for policy/knowledge lookup) or "agent" (for actions)
        """
        
        try:
            # For MVP, use a simple mock response
            if Config.OPENAI_API_KEY:
                response = await self._call_openai(prompt)
            else:
                response = self._mock_response(transcript)
            
            return Task(
                id=str(uuid.uuid4()),
                description=response["task_description"],
                generated_plan=response["plan"],
                task_type=response["task_type"]
            )
        except Exception as e:
            print(f"Error generating task: {e}")
            return self._fallback_task()
    
    async def _call_openai(self, prompt: str) -> dict:
        """Call OpenAI API"""
        response = openai.ChatCompletion.create(
            model=Config.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    
    def _mock_response(self, transcript: List[TranscriptEntry]) -> dict:
        """Mock response for testing without API key"""
        if any("order" in entry.text.lower() for entry in transcript):
            return {
                "task_description": "Look up order status for ORDER-12345",
                "plan": "1. Search order database\n2. Check shipping status\n3. Provide update to customer",
                "task_type": "rag"
            }
        return {
            "task_description": "Provide general assistance",
            "plan": "1. Understand customer issue\n2. Provide relevant information",
            "task_type": "rag"
        }
    
    def _fallback_task(self) -> Task:
        return Task(
            id=str(uuid.uuid4()),
            description="Process customer inquiry",
            generated_plan="Analyze conversation and provide assistance",
            task_type="rag"
        ) 