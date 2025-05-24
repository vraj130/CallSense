import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any
from utils.models import TranscriptEntry, Speaker
import os
import logging
import queue
import threading
import pyaudio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import assemblyai as aai
except ImportError:
    logger.error(
        "AssemblyAI package not found. Please install it with: pip install assemblyai"
    )
    raise


class SpeechToTextService:
    """Real-time Speech-to-Text service using AssemblyAI"""

    def __init__(self):
        self.is_running = False
        self.transcriber: Optional[aai.RealtimeTranscriber] = None
        self.microphone_stream: Optional[aai.extras.MicrophoneStream] = None
        self.transcript_queue = queue.Queue()  # Thread-safe queue
        self._loop = None
        self._audio = pyaudio.PyAudio()

        # Get API key from environment variables
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise ValueError(
                "ASSEMBLYAI_API_KEY environment variable is required"
            )

        # Set the API key
        aai.settings.api_key = api_key

        # List available audio devices
        self._list_audio_devices()

    def _list_audio_devices(self):
        """List available audio input devices"""
        logger.info("Available audio input devices:")
        for i in range(self._audio.get_device_count()):
            device_info = self._audio.get_device_info_by_index(i)
            max_input_channels = device_info.get("maxInputChannels", 0)
            if (
                isinstance(max_input_channels, (int, float))
                and max_input_channels > 0
            ):
                logger.info(f"Device {i}: {device_info.get('name')}")

    def _get_default_input_device(self) -> int:
        """Get the default input device index"""
        try:
            default_device = self._audio.get_default_input_device_info()
            device_index = default_device.get("index")
            if not isinstance(device_index, int):
                raise ValueError("Invalid device index")
            logger.info(
                f"Using default input device: {default_device.get('name')}"
            )
            return device_index
        except Exception as e:
            logger.warning(f"Could not get default input device: {e}")
            # Try to find any working input device
            for i in range(self._audio.get_device_count()):
                device_info = self._audio.get_device_info_by_index(i)
                max_input_channels = device_info.get("maxInputChannels", 0)
                if (
                    isinstance(max_input_channels, (int, float))
                    and max_input_channels > 0
                ):
                    logger.info(
                        f"Using input device: {device_info.get('name')}"
                    )
                    return i
            raise RuntimeError("No input devices found")

    async def start_transcription(
        self,
    ) -> AsyncGenerator[TranscriptEntry, None]:
        """Start real-time transcription service"""
        logger.info("Starting AssemblyAI transcription service")
        self.is_running = True
        self._loop = asyncio.get_running_loop()

        try:
            # Create the Real-Time transcriber
            self.transcriber = aai.RealtimeTranscriber(
                sample_rate=44_100,
                on_data=self._handle_transcript,
                on_error=self._handle_error,
                on_open=self._handle_open,
                on_close=self._handle_close,
            )

            if not self.transcriber:
                raise RuntimeError("Failed to create transcriber")

            # Start the connection
            self.transcriber.connect()

            # Open a microphone stream with specific device
            try:
                device_index = self._get_default_input_device()
                self.microphone_stream = aai.extras.MicrophoneStream(
                    device_index=device_index,
                    sample_rate=44_100,
                )
            except Exception as e:
                logger.error(f"Failed to initialize microphone: {e}")
                raise RuntimeError(f"Could not initialize microphone: {e}")

            if not self.microphone_stream:
                raise RuntimeError("Failed to create microphone stream")

            # Start streaming in a separate task
            asyncio.create_task(self._stream_audio())

            # Yield transcript entries as they come in
            while self.is_running:
                try:
                    # Use a timeout to allow checking is_running
                    entry = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.transcript_queue.get(timeout=0.1)
                    )
                    yield entry
                except queue.Empty:
                    continue

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            self.stop_transcription()

    async def _stream_audio(self):
        """Stream audio in a separate task"""
        if not self.transcriber or not self.microphone_stream:
            logger.error("Transcriber or microphone stream not initialized")
            self.stop_transcription()
            return

        try:
            self.transcriber.stream(self.microphone_stream)
        except Exception as e:
            logger.error(f"Audio streaming error: {e}")
            self.stop_transcription()

    def stop_transcription(self):
        """Stop the transcription service"""
        self.is_running = False
        if self.transcriber:
            self.transcriber.close()
        if self._audio:
            self._audio.terminate()
        logger.info("Transcription service stopped")

    def _handle_transcript(self, transcript: aai.RealtimeTranscript):
        """Handle incoming transcript data"""
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            # For now, we'll use a simple heuristic to determine speaker
            # In a real implementation, you might want to use a more sophisticated approach
            speaker = "customer"  # Default speaker

            # Create the transcript entry
            entry = TranscriptEntry(
                speaker=Speaker(speaker),
                text=transcript.text,
                timestamp=datetime.now(),
            )
            logger.info(f"Generated entry: {entry.speaker.value}: {entry.text}")

            # Add to thread-safe queue
            self.transcript_queue.put(entry)

    def _handle_error(self, error: aai.RealtimeError):
        """Handle transcription errors"""
        logger.error(f"Transcription error: {error}")

    def _handle_open(self, session_opened: aai.RealtimeSessionOpened):
        """Handle session open"""
        logger.info(f"Session opened: {session_opened.session_id}")

    def _handle_close(self):
        """Handle session close"""
        logger.info("Session closed")
