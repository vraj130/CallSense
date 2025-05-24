from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class Speaker(Enum):
    CUSTOMER = "customer"
    AGENT = "agent"

class TranscriptEntry(BaseModel):
    speaker: Speaker
    text: str
    timestamp: datetime = datetime.now()

class Task(BaseModel):
    id: str
    description: str
    generated_plan: List[str]  # Changed from str to List[str]
    task_type: str  # "rag" or "agent"
    status: str = "pending"  # pending, processing, completed, failed
    result: Optional[str] = None

class AppState(BaseModel):
    conversation_id: str
    transcript: List[TranscriptEntry] = []
    current_task: Optional[Task] = None
    task_history: List[Task] = []
    is_recording: bool = False