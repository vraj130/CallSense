import asyncio
import uuid
from datetime import datetime

from components.llm_service import LLMService
from utils.models import TranscriptEntry, Speaker, Task

async def main():
    print("Testing LLMService...")

    # Sample transcript data
    sample_transcript = [
    TranscriptEntry(speaker=Speaker.CUSTOMER, text="Hi, I'm Rachel Green. I placed an order two weeks ago and still haven’t received it.", timestamp=datetime.now()),
    TranscriptEntry(speaker=Speaker.CUSTOMER, text="The order number is ORDER-90345.", timestamp=datetime.now()),
    TranscriptEntry(speaker=Speaker.AGENT, text="Let me check, Rachel. Looks like ORDER-90345 was delayed due to weather conditions.", timestamp=datetime.now()),
    TranscriptEntry(speaker=Speaker.CUSTOMER, text="Oh I see. Can you let me know when I can expect it?", timestamp=datetime.now())
]


    llm_service = LLMService()

    print("Generating task from transcript...")

    generated_task = await llm_service.generate_task_from_transcript(sample_transcript)

    if generated_task:

        print(f"  Customer Name: {generated_task.customer_name}")
        print(f"  Order Number: {generated_task.order_number}")
        print(f"  Order Status: {generated_task.order_status}")
        

    else:
        print("Failed to generate task.")

if __name__ == "__main__":
    asyncio.run(main())
