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
    customer_name: Optional[str] = None
    order_number: Optional[str] = None
    order_status: Optional[str] = None
    issue_description: Optional[str] = None 
    description: str 
    generated_plan: List[str] = [] 
    task_type: str = "general_inquiry" 
    status: str = "pending"  
    result: Optional[str] = None

class AppState(BaseModel):
    conversation_id: str
    transcript: List[TranscriptEntry] = []
    current_task: Optional[Task] = None
    task_history: List[Task] = []
    is_recording: bool = False