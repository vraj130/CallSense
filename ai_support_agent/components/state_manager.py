import asyncio
from typing import Optional, List, Callable
from utils.models import AppState, TranscriptEntry, Task
import uuid

class StateManager:
    def __init__(self):
        self.state = AppState(conversation_id=str(uuid.uuid4()))
        self._listeners: List[Callable] = []
        self._lock = asyncio.Lock()
    
    async def add_transcript_entry(self, entry: TranscriptEntry):
        async with self._lock:
            self.state.transcript.append(entry)
            await self._notify_listeners()
    
    async def update_task(self, task: Task):
        async with self._lock:
            self.state.current_task = task
            if task.status in ["completed", "failed"]:
                self.state.task_history.append(task)
                self.state.current_task = None
            await self._notify_listeners()
    
    async def get_transcript(self) -> List[TranscriptEntry]:
        async with self._lock:
            return self.state.transcript.copy()
    
    def add_listener(self, callback: Callable):
        self._listeners.append(callback)
    
    async def _notify_listeners(self):
        for listener in self._listeners:
            if asyncio.iscoroutinefunction(listener):
                await listener(self.state)
            else:
                listener(self.state)
    
    def get_state(self) -> AppState:
        return self.state.copy() 