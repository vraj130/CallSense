import asyncio
import websockets
import json
import threading
import queue
import pyaudio
import wave
import tempfile
import os
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class STTProvider(Enum):
    WHISPER = "whisper"
    OPENAI_API = "openai_api"
    GOOGLE_API = "google_api"
    AZURE_API = "azure_api"


@dataclass
class TranscriptionResult:
    text: str
    confidence: Optional[float] = None
    is_final: bool = True
    provider: Optional[str] = None
    timestamp: Optional[float] = None


class STTEngine(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        pass


class WhisperEngine(STTEngine):
    def __init__(self, model_size: str = "base"):
        try:
            import whisper

            self.model = whisper.load_model(model_size)
            logger.info(f"Loaded Whisper model: {model_size}")
        except ImportError:
            raise ImportError("pip install openai-whisper")

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        try:
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.model.transcribe, temp_path
            )

            return TranscriptionResult(
                text=result["text"].strip(), provider="whisper", is_final=True
            )
        finally:
            os.unlink(temp_path)

    def supports_streaming(self) -> bool:
        return False


class OpenAIEngine(STTEngine):
    def __init__(self, api_key: str):
        try:
            import openai

            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("pip install openai")

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        try:
            with open(temp_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="json"
                )

            return TranscriptionResult(
                text=response.text.strip(), provider="openai", is_final=True
            )
        finally:
            os.unlink(temp_path)

    def supports_streaming(self) -> bool:
        return False


class GoogleEngine(STTEngine):
    def __init__(self, credentials_path: str):
        try:
            from google.cloud import speech

            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            self.client = speech.SpeechClient()
        except ImportError:
            raise ImportError("pip install google-cloud-speech")

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        from google.cloud import speech

        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        response = self.client.recognize(config=config, audio=audio)

        if response.results:
            result = response.results[0]
            return TranscriptionResult(
                text=result.alternatives[0].transcript,
                confidence=result.alternatives[0].confidence,
                provider="google",
                is_final=True,
            )

        return TranscriptionResult(text="", provider="google")

    def supports_streaming(self) -> bool:
        return True


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        self.channels = 1
        self.is_recording = False
        self.audio_queue = queue.Queue()

    def start_recording(self):
        """Start recording audio in background thread"""

        def record_worker():
            p = pyaudio.PyAudio()
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            logger.info("Recording started")
            frames = []
            silence_count = 0

            try:
                while self.is_recording:
                    data = stream.read(
                        self.chunk_size, exception_on_overflow=False
                    )
                    frames.append(data)

                    # Simple voice activity detection based on amplitude
                    amplitude = max(data)
                    if amplitude > 1000:  # Adjust threshold as needed
                        silence_count = 0
                    else:
                        silence_count += 1

                    # If we have 2 seconds of audio and recent silence, process it
                    if (
                        len(frames) > (self.sample_rate // self.chunk_size * 2)
                        and silence_count > 20
                    ):
                        audio_data = self._frames_to_wav(frames)
                        self.audio_queue.put(audio_data)
                        frames = []
                        silence_count = 0

            except Exception as e:
                logger.error(f"Recording error: {e}")
            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()
                logger.info("Recording stopped")

        self.is_recording = True
        self.record_thread = threading.Thread(target=record_worker)
        self.record_thread.start()

    def stop_recording(self):
        self.is_recording = False
        if hasattr(self, "record_thread"):
            self.record_thread.join()

    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[bytes]:
        """Get next audio chunk from queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _frames_to_wav(self, frames: list) -> bytes:
        """Convert audio frames to WAV bytes"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with wave.open(temp_file.name, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(frames))

            temp_file.seek(0)
            return temp_file.read()


class SpeechToTextBackend:
    def __init__(self, engine: STTEngine):
        self.engine = engine
        self.recorder = AudioRecorder()
        self.websocket_clients = set()
        self.is_running = False

    async def add_websocket_client(self, websocket):
        """Add a websocket client for streaming"""
        self.websocket_clients.add(websocket)
        logger.info(
            f"Client connected. Total clients: {len(self.websocket_clients)}"
        )

    async def remove_websocket_client(self, websocket):
        """Remove a websocket client"""
        self.websocket_clients.discard(websocket)
        logger.info(
            f"Client disconnected. Total clients: {len(self.websocket_clients)}"
        )

    async def broadcast_transcription(self, result: TranscriptionResult):
        """Send transcription to all connected clients"""
        if not self.websocket_clients:
            return

        message = {
            "type": "transcription",
            "text": result.text,
            "confidence": result.confidence,
            "is_final": result.is_final,
            "provider": result.provider,
            "timestamp": result.timestamp,
        }

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.websocket_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            await self.remove_websocket_client(client)

    async def start_processing(self):
        """Start the main processing loop"""
        self.is_running = True
        self.recorder.start_recording()

        logger.info("Speech processing started")

        while self.is_running:
            # Get audio chunk from recorder
            audio_data = self.recorder.get_audio_chunk(timeout=0.5)

            if audio_data:
                try:
                    # Transcribe audio
                    result = await self.engine.transcribe(audio_data)

                    if (
                        result.text.strip()
                    ):  # Only send non-empty transcriptions
                        logger.info(f"Transcribed: {result.text}")
                        await self.broadcast_transcription(result)

                except Exception as e:
                    logger.error(f"Transcription error: {e}")

            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

    def stop_processing(self):
        """Stop processing"""
        self.is_running = False
        self.recorder.stop_recording()
        logger.info("Speech processing stopped")


# WebSocket server handler
async def websocket_handler(websocket, path, backend: SpeechToTextBackend):
    await backend.add_websocket_client(websocket)
    try:
        async for message in websocket:
            # Handle client messages if needed
            data = json.loads(message)
            if data.get("type") == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await backend.remove_websocket_client(websocket)


# Main server
class STTServer:
    def __init__(self, provider: STTProvider, **kwargs):
        self.backend = self._create_backend(provider, **kwargs)
        self.server = None

    def _create_backend(
        self, provider: STTProvider, **kwargs
    ) -> SpeechToTextBackend:
        """Create appropriate STT engine based on provider"""
        if provider == STTProvider.WHISPER:
            model_size = kwargs.get("model_size", "base")
            engine = WhisperEngine(model_size)
        elif provider == STTProvider.OPENAI_API:
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("OpenAI API key required")
            engine = OpenAIEngine(api_key)
        elif provider == STTProvider.GOOGLE_API:
            credentials_path = kwargs.get("credentials_path")
            if not credentials_path:
                raise ValueError("Google credentials path required")
            engine = GoogleEngine(credentials_path)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        return SpeechToTextBackend(engine)

    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server"""
        handler = lambda ws, path: websocket_handler(ws, path, self.backend)

        self.server = await websockets.serve(handler, host, port)
        logger.info(f"STT Server started on ws://{host}:{port}")

        # Start processing in background
        processing_task = asyncio.create_task(self.backend.start_processing())

        try:
            await self.server.wait_closed()
        finally:
            self.backend.stop_processing()
            await processing_task


# Example usage and configuration
async def main():
    # Choose your provider
    # Option 1: Offline Whisper
    server = STTServer(STTProvider.WHISPER, model_size="base")

    # Option 2: OpenAI API
    # server = STTServer(STTProvider.OPENAI_API, api_key="your-openai-key")

    # Option 3: Google Cloud
    # server = STTServer(STTProvider.GOOGLE_API, credentials_path="path/to/credentials.json")

    await server.start_server(host="localhost", port=8765)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
