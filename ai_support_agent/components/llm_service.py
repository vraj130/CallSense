import openai
from openai import AsyncOpenAI
from typing import List
import json
from config import Config
from utils.models import TranscriptEntry, Task
import uuid

class LLMService:
    def __init__(self):
        # Initialize the AsyncOpenAI client
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Load system prompt from file specified in config
        try:
            with open(Config.LLM_SYSTEM_PROMPT_PATH, 'r') as f:
                self.system_prompt = f.read().strip()
        except Exception as e:
            print(f"[Warning] Failed to load system prompt from file. Using default. Error: {e}")
            self.system_prompt = "You are a helpful customer support assistant."

    async def generate_task_from_transcript(self, transcript: List[TranscriptEntry]) -> Task:
        """Generate task/plan from conversation transcript"""
        print("\n=== LLM Service: generate_task_from_transcript ===")
        
        # Format transcript for LLM
        conversation = "\n".join([f"{entry.speaker.value}: {entry.text}" for entry in transcript])
        
        # The system_prompt (loaded from system_prompt.txt) contains the detailed instructions
        # on what to extract and the JSON format. The user prompt here just needs to provide the transcript.
        prompt = f"Transcript:\n{conversation}"
        
        try:
            print("Calling OpenAI API...")
            # Always call OpenAI API
            response = await self._call_openai(prompt)
            print("OpenAI API call completed")



            # task = Task(
            #     id=str(uuid.uuid4()),
            #     customer_name=response.get("customer_name"),
            #     order_number=response.get("order_number"),
            #     order_status=response.get("order_status"),
            #     issue_description=response.get("issue_description"), # Store raw issue_description
            #     description=response.get("issue_description", "No description provided"), # Map to main description
            #     generated_plan=response.get("generated_plan", ["Generate a plan to resolve the issue"]), # to be implemented by @Vijay
            #     task_type = response.get("generated_plan", "rag")# will use defaults from Task model if not in response
            # )
            
            # hardcoding for testing
            task = Task(
                id=str(uuid.uuid4()),
                customer_name="Alicia",
                order_number="12345",
                order_status=response.get("order_status"),
                issue_description=response.get("issue_description"), # Store raw issue_description
                description=response.get("issue_description", "No description provided"), # Map to main description
                generated_plan=response.get("generated_plan", ["Generate a plan to resolve the issue"]), # to be implemented by @Vijay
                task_type = response.get("generated_plan", "rag")# will use defaults from Task model if not in response
            )

            print(f"[LLMService] description: {task.description}")
            print(f"[LLMService] generated_plan: {task.generated_plan}")
            print(f"[LLMService] task_type: {task.task_type}")
            print(f"[LLMService] customer_name: {task.customer_name}")
            print(f"[LLMService] order_number: {task.order_number}")
            print(f"[LLMService] order_status: {task.order_status}")
            print(f"[LLMService] issue_description: {task.issue_description}")
            # Map LLM response to Task model fields
            return task
        
        except Exception as e:
            print(f"[Error] Failed to generate task from LLM: {e}")
            return self._fallback_task()

    async def _call_openai(self, prompt: str) -> dict:
        """Call OpenAI API using the new v1.x.x syntax"""
        response = await self.client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw_content = response.choices[0].message.content
        # print(f"--- LLM Raw Response Content ---\n{raw_content}\n--------------------------------")

        # Strip markdown fences if present
        cleaned_content = raw_content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[len("```json"):].strip()
        if cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[len("```"):].strip()
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-len("```")].strip()
            
        return json.loads(cleaned_content)

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
            description="Could not process customer inquiry due to an internal error.",
            issue_description="Could not process customer inquiry due to an internal error.",
            # generated_plan and task_type will use defaults from Task model
        )
