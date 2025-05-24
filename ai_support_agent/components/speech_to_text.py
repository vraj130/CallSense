import asyncio
from datetime import datetime
from typing import AsyncGenerator
from utils.models import TranscriptEntry, Speaker

class SpeechToTextService:
    """Mock Speech-to-Text service for MVP"""
    
    def __init__(self):
        self.is_running = False
        
    async def start_transcription(self):
        """Start transcription service"""
        print("\n=== Starting mock transcription service ===")
        self.is_running = True
        
        # Mock conversation for testing
        mock_conversation = [
            ("customer", "Hi, I need help with my order"),
            ("agent", "Hello! I'd be happy to help. Could you please provide your order number?"),
            ("customer", "Yes, it's ORDER-12345"),
            ("agent", "Thank you. Let me check the status of your order.")
        ]
        
        for speaker, text in mock_conversation:
            if not self.is_running:
                break
                
            print(f"\nGenerating mock entry: {speaker}: {text}")
            entry = TranscriptEntry(
                speaker=Speaker(speaker),
                text=text,
                timestamp=datetime.now()
            )
            print(f"Yielding entry: {entry.speaker.value}: {entry.text}")
            yield entry
            await asyncio.sleep(3)  # Simulate real-time transcription delay
    
    def stop_transcription(self):
        self.is_running = False 