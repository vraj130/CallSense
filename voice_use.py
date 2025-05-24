#!/usr/bin/env python3
"""
Voice-controlled browser automation system
Uses OpenAI Whisper for local speech-to-text with extensible design for future API integration
"""

import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable, Any
import tempfile
import wave

import pyaudio
import whisper
from browser_use import Agent
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeechToTextBase(ABC):
    """Abstract base class for speech-to-text implementations"""

    @abstractmethod
    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file to text"""
        pass


class WhisperSTT(SpeechToTextBase):
    """Local OpenAI Whisper implementation"""

    def __init__(self, model_name: str = "base"):
        """
        Initialize Whisper model

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        logger.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        logger.info("Whisper model loaded successfully")

    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file using local Whisper model"""
        try:
            # Run Whisper in thread pool to avoid blocking async loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self.model.transcribe(audio_file_path)
            )
            # Whisper returns a dict with 'text' key containing a string
            if (
                isinstance(result, dict)
                and "text" in result
                and isinstance(result["text"], str)
            ):
                return result["text"].strip()
            return ""
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return ""


# class APIBasedSTT(SpeechToTextBase):
#     """Placeholder for future API-based implementations (OpenAI API, Azure, etc.)"""

#     def __init__(self, api_key: str, service: str = "openai"):
#         self.api_key = api_key
#         self.service = service

#     async def transcribe(self, audio_file_path: str) -> str:
#         """Future implementation for API-based transcription"""
#         # TODO: Implement API calls to OpenAI Whisper API, Azure Speech, etc.
#         raise NotImplementedError("API-based STT not yet implemented")


class VoiceRecorder:
    """Handle audio recording from microphone"""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        format: int = pyaudio.paInt16,
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = format
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.frames = []

    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        self.frames = []

        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

        logger.info("Started recording... Press Enter to stop")

        # Record in separate thread
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.start()

    def stop_recording(self) -> str:
        """Stop recording and save to temporary file"""
        self.is_recording = False

        if hasattr(self, "recording_thread"):
            self.recording_thread.join()

        if hasattr(self, "stream"):
            self.stream.stop_stream()
            self.stream.close()

        # Save to temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        with wave.open(temp_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(self.frames))

        logger.info(f"Audio saved to: {temp_path}")
        return temp_path

    def _record_audio(self):
        """Internal method to record audio in separate thread"""
        while self.is_recording:
            try:
                data = self.stream.read(
                    self.chunk_size, exception_on_overflow=False
                )
                self.frames.append(data)
            except Exception as e:
                logger.error(f"Recording error: {e}")
                break

    def __del__(self):
        """Cleanup audio resources"""
        if hasattr(self, "audio"):
            self.audio.terminate()


class BrowserController:
    """Handle browser automation using browser-use"""

    def __init__(self, llm_model: str = "gpt-4"):
        """
        Initialize browser controller

        Args:
            llm_model: LLM model to use for browser-use agent
        """
        self.llm = ChatOpenAI(model=llm_model)
        self.agent = None

    async def execute_command(self, command: str) -> str:
        """
        Execute voice command in browser

        Args:
            command: Natural language command to execute

        Returns:
            Result description
        """
        try:
            if not self.agent:
                self.agent = Agent(
                    task=command,
                    llm=self.llm,
                )

            logger.info(f"Executing browser command: {command}")
            result = await self.agent.run()
            return f"Command executed: {command}"

        except Exception as e:
            error_msg = f"Failed to execute command '{command}': {e}"
            logger.error(error_msg)
            return error_msg


class VoiceBrowserController:
    """Main controller class that orchestrates voice recording, STT, and browser control"""

    def __init__(
        self, stt_impl: SpeechToTextBase, browser_controller: BrowserController
    ):
        self.stt = stt_impl
        self.browser = browser_controller
        self.recorder = VoiceRecorder()
        self.is_running = False

    async def start_listening(self):
        """Start the voice control loop"""
        self.is_running = True
        logger.info("Voice browser controller started. Say 'exit' to quit.")

        while self.is_running:
            try:
                await self._process_voice_command()
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in voice processing: {e}")
                await asyncio.sleep(1)

        logger.info("Voice browser controller stopped")

    async def _process_voice_command(self):
        """Process a single voice command"""
        print("\n--- Ready for voice command ---")
        print("Press Enter to start recording...")
        input()  # Wait for user input

        # Record audio
        self.recorder.start_recording()
        print("Recording... Press Enter to stop")
        input()  # Wait for user to stop recording

        audio_file = self.recorder.stop_recording()

        try:
            # Transcribe audio
            print("Transcribing...")
            text = await self.stt.transcribe(audio_file)

            if not text:
                print("No speech detected or transcription failed")
                return

            print(f"You said: '{text}'")

            # Check for exit command
            if "exit" in text.lower() or "quit" in text.lower():
                self.is_running = False
                return

            # Execute browser command
            print("Executing command...")
            result = await self.browser.execute_command(text)
            print(f"Result: {result}")

        finally:
            # Clean up temporary audio file
            try:
                Path(audio_file).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file {audio_file}: {e}")


async def main():
    """Main entry point"""
    try:
        # Initialize components
        print("Initializing voice browser controller...")

        # Initialize STT (you can switch to APIBasedSTT later)
        stt = WhisperSTT(model_name="base")  # or "small", "medium", "large"

        # Initialize browser controller
        browser = BrowserController()

        # Initialize main controller
        controller = VoiceBrowserController(stt, browser)

        # Start listening
        await controller.start_listening()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
