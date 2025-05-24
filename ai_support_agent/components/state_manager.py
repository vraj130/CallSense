import asyncio
from typing import Optional, List, Callable
from utils.models import AppState, TranscriptEntry, Task
import uuid
import threading


class StateManager:
    def __init__(self):
        self.state = AppState(conversation_id=str(uuid.uuid4()))
        self._listeners: List[Callable] = []
        self._lock = (
            threading.RLock()
        )  # Use threading lock instead of asyncio lock

    async def add_transcript_entry(self, entry: TranscriptEntry):
        with self._lock:
            print(
                f"\nAdding transcript entry: {entry.speaker.value}: {entry.text}"
            )
            self.state.transcript.append(entry)
            # Don't await listeners in async context when called from different threads
            self._notify_listeners_sync()

    async def update_task(self, task: Task):
        with self._lock:
            self.state.current_task = task
            if task.status in ["completed", "failed"]:
                self.state.task_history.append(task)
                self.state.current_task = None
            self._notify_listeners_sync()

    async def get_transcript(self) -> List[TranscriptEntry]:
        with self._lock:
            print(
                f"\nGetting transcript, current length: {len(self.state.transcript)}"
            )
            return self.state.transcript.copy()

    def add_listener(self, callback: Callable):
        self._listeners.append(callback)

    def _notify_listeners_sync(self):
        """Synchronous notification for thread safety"""
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    # Skip async listeners when called from different threads
                    continue
                else:
                    listener(self.state)
            except Exception as e:
                print(f"Error notifying listener: {e}")

    def get_state(self) -> AppState:
        """Thread-safe synchronous method to get current state"""
        with self._lock:
            return self.state.model_copy()
