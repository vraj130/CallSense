import asyncio
from typing import Optional, List, Callable
from utils.models import AppState, TranscriptEntry, Task
import uuid
import threading


class StateManager:
    def __init__(self, transcript_storage=None):
        self.state = AppState(conversation_id=str(uuid.uuid4()))
        self._listeners: List[Callable] = []
        self._lock = threading.RLock()
        self.transcript_storage = transcript_storage
        self._auto_save_threshold = 5  # Auto-save every 5 entries

    async def add_transcript_entry(self, entry: TranscriptEntry):
        with self._lock:
            print(
                f"\nAdding transcript entry: {entry.speaker.value}: {entry.text}"
            )
            self.state.transcript.append(entry)

            # Auto-save transcript periodically
            if (
                self.transcript_storage
                and len(self.state.transcript) % self._auto_save_threshold == 0
            ):
                asyncio.create_task(self._auto_save_transcript())

            self._notify_listeners_sync()

    async def _auto_save_transcript(self):
        """Auto-save transcript in background"""
        try:
            if self.transcript_storage:
                filename = await self.transcript_storage.auto_save_transcript(
                    self.state
                )
                if filename:
                    print(f"Auto-saved transcript to: {filename}")
        except Exception as e:
            print(f"Error in auto-save: {e}")

    async def save_current_transcript(self) -> Optional[str]:
        """Manually save current transcript"""
        if not self.transcript_storage:
            print("No transcript storage service configured")
            return None

        try:
            filename = await self.transcript_storage.save_transcript(
                self.state.conversation_id, self.state.transcript
            )
            print(f"Transcript manually saved to: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving transcript: {e}")
            return None

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

    def clear_transcript(self):
        """Clear current transcript and start new conversation"""
        with self._lock:
            self.state.transcript.clear()
            self.state.conversation_id = str(uuid.uuid4())
            print(f"Started new conversation: {self.state.conversation_id}")
            self._notify_listeners_sync()
