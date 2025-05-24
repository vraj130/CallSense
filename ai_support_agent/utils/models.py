"""
Data models for the Customer Support AI Agent application.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid


class Speaker(Enum):
    """Enum for different speakers in the conversation"""

    CUSTOMER = "customer"
    AGENT = "agent"
    SPEAKER = "speaker"  # Generic speaker when we can't differentiate

    def __str__(self):
        return self.value


class TaskStatus(Enum):
    """Enum for task statuses"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    """Enum for task types"""

    RAG = "rag"  # Information lookup/retrieval
    AGENT = "agent"  # Action required


class TranscriptEntry(BaseModel):
    """Individual entry in a conversation transcript"""

    speaker: Speaker
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic configuration"""

        use_enum_values = False  # Keep enum objects, don't convert to values

    def get_speaker_value(self) -> str:
        """Get speaker value safely"""
        return (
            self.speaker.value
            if hasattr(self.speaker, "value")
            else str(self.speaker)
        )


class Task(BaseModel):
    """Task generated from conversation analysis"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Basic task information
    customer_name: Optional[str] = "Customer"
    order_number: Optional[str] = None
    order_status: Optional[str] = None
    issue_description: str
    description: str  # Main description (usually same as issue_description)

    # Task execution details
    generated_plan: List[str] = Field(
        default_factory=lambda: ["Review customer request"]
    )
    task_type: str = "rag"  # "rag" or "agent"
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    result: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # Layman-friendly fields for customer service operators
    issue_category: str = (
        "General Inquiry"  # e.g., "Order Status", "Refund Request", "Product Issue"
    )
    urgency_level: str = "Medium"  # "Low", "Medium", "High"
    operator_instructions: str = (
        "Review customer request and provide assistance"
    )
    verification_points: List[str] = Field(
        default_factory=list
    )  # Things operator should verify
    suggested_response: str = (
        "Thank you for contacting us. How can I help you today?"
    )

    class Config:
        """Pydantic configuration"""

        use_enum_values = True

    def update_status(self, new_status: str, result: Optional[str] = None):
        """Update task status and result"""
        self.status = new_status
        self.updated_at = datetime.now()
        if result:
            self.result = result


class AppState(BaseModel):
    """Application state containing all conversation and task data"""

    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transcript: List[TranscriptEntry] = Field(default_factory=list)
    current_task: Optional[Task] = None
    task_history: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic configuration"""

        use_enum_values = True

    def add_transcript_entry(self, entry: TranscriptEntry):
        """Add a new transcript entry"""
        self.transcript.append(entry)

    def set_current_task(self, task: Task):
        """Set the current active task"""
        self.current_task = task

    def complete_current_task(self, result: str):
        """Complete the current task and move it to history"""
        if self.current_task:
            self.current_task.update_status("completed", result)
            self.task_history.append(self.current_task)
            self.current_task = None

    def get_transcript_text(self) -> str:
        """Get transcript as plain text"""
        lines = []
        for entry in self.transcript:
            timestamp_str = entry.timestamp.strftime("%H:%M:%S")
            lines.append(
                f"[{timestamp_str}] {entry.speaker.value}: {entry.text}"
            )
        return "\n".join(lines)

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation"""
        total_entries = len(self.transcript)
        if total_entries == 0:
            return "No conversation yet"

        latest_entry = self.transcript[-1]
        return f"{total_entries} messages, latest: {latest_entry.text[:50]}..."


# Utility functions for working with models


def create_transcript_entry(
    speaker: str, text: str, timestamp: Optional[datetime] = None
) -> TranscriptEntry:
    """Create a new transcript entry"""
    return TranscriptEntry(
        speaker=Speaker(speaker),
        text=text,
        timestamp=timestamp or datetime.now(),
    )


def create_task(
    issue_description: str,
    customer_name: str = "Customer",
    task_type: str = "rag",
    order_number: Optional[str] = None,
    urgency_level: str = "Medium",
    issue_category: str = "General Inquiry",
) -> Task:
    """Create a new task with default values"""
    return Task(
        issue_description=issue_description,
        description=issue_description,
        customer_name=customer_name,
        task_type=task_type,
        order_number=order_number,
        urgency_level=urgency_level,
        issue_category=issue_category,
    )


def create_app_state(conversation_id: Optional[str] = None) -> AppState:
    """Create a new application state"""
    return AppState(conversation_id=conversation_id or str(uuid.uuid4()))


# Constants for commonly used values

ISSUE_CATEGORIES = [
    "Order Status",
    "Refund Request",
    "Product Issue",
    "Account Help",
    "General Inquiry",
    "Complaint",
    "Shipping Issue",
    "Payment Issue",
]

URGENCY_LEVELS = ["Low", "Medium", "High"]

TASK_TYPES = ["rag", "agent"]

TASK_STATUSES = ["pending", "processing", "completed", "failed"]
