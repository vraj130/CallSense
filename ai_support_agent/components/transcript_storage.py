import os
import aiofiles
from datetime import datetime
from typing import List, Optional
from utils.models import TranscriptEntry, AppState


class TranscriptStorageService:
    """Service for storing and retrieving conversation transcripts as plain text"""

    def __init__(self, storage_dir: str = "data/transcripts"):
        self.storage_dir = storage_dir
        self.ensure_storage_dir()

    def ensure_storage_dir(self):
        """Ensure the storage directory exists"""
        os.makedirs(self.storage_dir, exist_ok=True)

    def get_transcript_filename(self, conversation_id: str) -> str:
        """Generate filename for a conversation transcript"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(
            self.storage_dir, f"transcript_{conversation_id}_{timestamp}.txt"
        )

    async def save_transcript(
        self, conversation_id: str, transcript: List[TranscriptEntry]
    ) -> str:
        """Save transcript to plain text file and return the filename"""
        filename = self.get_transcript_filename(conversation_id)

        # Convert transcript entries to plain text
        lines = []
        lines.append(f"Conversation ID: {conversation_id}")
        lines.append(
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append("=" * 50)
        lines.append("")

        # Add each transcript entry as plain text
        for entry in transcript:
            timestamp_str = entry.timestamp.strftime("%H:%M:%S")
            lines.append(
                f"[{timestamp_str}] {entry.speaker.value}: {entry.text}"
            )

        lines.append("")
        lines.append("=" * 50)
        lines.append(f"Total entries: {len(transcript)}")

        try:
            async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                await f.write("\n".join(lines))

            print(f"Transcript saved to: {filename}")
            return filename

        except Exception as e:
            print(f"Error saving transcript: {e}")
            raise

    async def load_transcript_text(self, filename: str) -> Optional[str]:
        """Load transcript as plain text"""
        try:
            async with aiofiles.open(filename, "r", encoding="utf-8") as f:
                content = await f.read()
            return content

        except Exception as e:
            print(f"Error loading transcript from {filename}: {e}")
            return None

    def get_transcript_for_llm(self, transcript: List[TranscriptEntry]) -> str:
        """Convert transcript entries to clean text for LLM processing"""
        if not transcript:
            return "No conversation available."

        lines = []
        lines.append("Customer Support Conversation:")
        lines.append("-" * 30)

        for entry in transcript:
            # Simple format for LLM - just speaker and text
            lines.append(f"{entry.speaker.value}: {entry.text}")

        return "\n".join(lines)

    async def auto_save_transcript(self, state: AppState) -> Optional[str]:
        """Auto-save transcript when it has entries"""
        if not state.transcript:
            return None

        try:
            filename = await self.save_transcript(
                state.conversation_id, state.transcript
            )
            return filename
        except Exception as e:
            print(f"Error in auto-save: {e}")
            return None

    def list_transcript_files(self) -> List[str]:
        """List all transcript files in storage directory"""
        try:
            files = [
                f
                for f in os.listdir(self.storage_dir)
                if f.startswith("transcript_") and f.endswith(".txt")
            ]
            return sorted(files, reverse=True)  # Most recent first
        except Exception as e:
            print(f"Error listing transcript files: {e}")
            return []

    async def get_latest_transcript_content(self) -> Optional[str]:
        """Get the content of the most recent transcript file"""
        files = self.list_transcript_files()
        if not files:
            return None

        latest_file = os.path.join(self.storage_dir, files[0])
        return await self.load_transcript_text(latest_file)
