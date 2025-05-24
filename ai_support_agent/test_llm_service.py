import asyncio
import uuid
from datetime import datetime

from .components.llm_service import LLMService
from .utils.models import TranscriptEntry, Speaker, Task

async def main():
    print("Testing LLMService...")

    # Sample transcript data
    sample_transcript = [
        TranscriptEntry(speaker=Speaker.CUSTOMER, text="Hello, I'm having trouble with my internet connection.", timestamp=datetime.now()),
        TranscriptEntry(speaker=Speaker.AGENT, text="Hi there! I can help with that. What seems to be the problem?", timestamp=datetime.now()),
        TranscriptEntry(speaker=Speaker.CUSTOMER, text="It keeps dropping out every few minutes.", timestamp=datetime.now()),
    ]

    llm_service = LLMService()

    print("Generating task from transcript...")
    # Ensure your OPENAI_API_KEY is in a .env file in the root of hackathon-repo 
    # or the mock response will be used.
    generated_task = await llm_service.generate_task_from_transcript(sample_transcript)

    if generated_task:
        print("\nGenerated Task:")
        print(f"  ID: {generated_task.id}")
        print(f"  Description: {generated_task.description}")
        print(f"  Generated Plan: {generated_task.generated_plan}")
        print(f"  Task Type: {generated_task.task_type}")
        print(f"  Status: {generated_task.status}")
        print(f"  Result: {generated_task.result}")
    else:
        print("Failed to generate task.")

if __name__ == "__main__":
    asyncio.run(main())
