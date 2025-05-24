import asyncio
from datetime import datetime
from typing import AsyncGenerator
from utils.models import TranscriptEntry, Speaker
import random

class SpeechToTextService:
    """Mock Speech-to-Text service for MVP"""
    
    def __init__(self):
        self.is_running = False
        
    async def start_transcription(self) -> AsyncGenerator[TranscriptEntry, None]:
        """Simulate real-time transcription"""
        self.is_running = True
        
        # Mock conversation snippets
        mock_conversation = [
            (Speaker.CUSTOMER, "Hello, I'm having trouble with my order"),
            (Speaker.AGENT, "I'd be happy to help you with that. Can you provide your order number?"),
            (Speaker.CUSTOMER, "Yes, it's ORDER-12345"),
            (Speaker.AGENT, "Let me look that up for you"),
        ]
        
        idx = 0
        while self.is_running:
            if idx < len(mock_conversation):
                speaker, text = mock_conversation[idx]
                yield TranscriptEntry(
                    speaker=speaker,
                    text=text,
                    timestamp=datetime.now()
                )
                idx += 1
            
            await asyncio.sleep(3)  # Simulate delay between utterances
    
    def stop_transcription(self):
        self.is_running = False 