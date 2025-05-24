import asyncio
import threading
import time
from components.speech_to_text import SpeechToTextService
from components.llm_service import LLMService
from components.orchestrator import Orchestrator
from components.rag_service import RAGService
from components.ai_agent import AIAgent
from components.state_manager import StateManager
from frontend.gradio_app import GradioInterface
from config import Config


class CustomerSupportAIApp:
    def __init__(self):
        # Initialize components
        self.state_manager = StateManager()
        self.speech_service = SpeechToTextService()
        self.llm_service = LLMService()
        self.rag_service = RAGService()
        self.ai_agent = AIAgent()
        self.orchestrator = Orchestrator(
            self.rag_service, self.ai_agent, self.state_manager
        )
        self.frontend = GradioInterface(self.state_manager)
        self.transcription_task = None
        self.background_loop = None
        self.background_thread = None
        self.is_running = False

    async def initialize(self):
        """Initialize all services"""
        try:
            await self.rag_service.initialize()
            await self.ai_agent.initialize()
            print("All services initialized")
        except Exception as e:
            print(f"Error initializing services: {e}")
            raise

    async def _transcription_loop(self):
        """Background task for transcription using callback approach"""
        print("\n=== Starting transcription loop (callback approach) ===")

        def on_transcript_entry(entry):
            """Callback for when a transcript entry is received"""
            print(
                f"\nReceived entry in callback: {entry.speaker.value}: {entry.text}"
            )

            # Direct approach - add to state manager synchronously
            try:
                print("Adding transcript entry directly...")
                # Since we're in a callback from a different thread, we need to be careful
                # Let's add it directly to the state without async
                with self.state_manager._lock:
                    print(
                        f"Adding transcript entry: {entry.speaker.value}: {entry.text}"
                    )
                    self.state_manager.state.transcript.append(entry)
                    print("Entry successfully added to state manager")

                    # Verify the entry was added
                    current_count = len(self.state_manager.state.transcript)
                    print(f"Current transcript count: {current_count}")

            except Exception as e:
                print(f"Error adding entry to state manager: {e}")
                import traceback

                traceback.print_exc()

        # Set up the callback
        self.speech_service.set_entry_callback(on_transcript_entry)

        # Start transcription with callback
        await self.speech_service.start_transcription_with_callback()

    def run_background_loop(self):
        """Run the background async loop in a separate thread"""
        try:
            self.background_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.background_loop)

            # Initialize services
            self.background_loop.run_until_complete(self.initialize())

            # Start transcription loop
            self.background_loop.run_until_complete(self._transcription_loop())

        except Exception as e:
            print(f"Error in background loop: {e}")
        finally:
            if self.background_loop:
                self.background_loop.close()

    def start_background_services(self):
        """Start background services in a separate thread"""
        self.is_running = True
        self.background_thread = threading.Thread(
            target=self.run_background_loop, daemon=True
        )
        self.background_thread.start()
        print("Background services started")

        # Give the background thread time to initialize
        time.sleep(2)

    def process_trigger_sync(self):
        """Process trigger in sync context for Gradio"""
        print("\n=== Processing trigger ===")
        transcript = self.state_manager.get_state().transcript
        print(f"Current transcript length: {len(transcript)}")

        if not transcript:
            print("No transcript found")
            return "No conversation to process", ""

        try:
            # Create a new event loop for this operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                print("Generating task from transcript...")
                task = loop.run_until_complete(
                    self.llm_service.generate_task_from_transcript(transcript)
                )
                print(f"Generated task: {task.description}")

                print("Routing task...")
                result = loop.run_until_complete(
                    self.orchestrator.route_task(task)
                )
                print(f"Task result: {result}")

                return "Task completed successfully", result

            finally:
                loop.close()

        except Exception as e:
            print(f"Error in process_trigger_sync: {str(e)}")
            return f"Error: {str(e)}", ""

    def stop(self):
        """Stop all services"""
        self.is_running = False
        if self.speech_service:
            self.speech_service.stop_transcription()
        if self.background_loop and not self.background_loop.is_closed():
            self.background_loop.call_soon_threadsafe(self.background_loop.stop)

    def run(self):
        """Run the application"""
        try:
            # Start background services
            self.start_background_services()

            # Add a manual test entry to verify UI updates
            print("Adding manual test entry...")
            from utils.models import TranscriptEntry, Speaker
            from datetime import datetime

            test_entry = TranscriptEntry(
                speaker=Speaker.CUSTOMER,
                text="Manual test entry - Hello! This should appear in the UI.",
                timestamp=datetime.now(),
            )

            # Add directly to state
            with self.state_manager._lock:
                self.state_manager.state.transcript.append(test_entry)

            print(
                f"Manual entry added. Total entries: {len(self.state_manager.get_state().transcript)}"
            )

            # Create and launch Gradio interface
            interface = self.frontend.create_interface(
                trigger_callback=self.process_trigger_sync
            )

            print("Launching Gradio interface...")
            interface.launch(
                server_port=Config.GRADIO_PORT, share=False, inbrowser=True
            )

        except Exception as e:
            print(f"Error running application: {e}")
            self.stop()
            raise


def main():
    """Entry point"""
    app = CustomerSupportAIApp()

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.stop()
    except Exception as e:
        print(f"Application error: {e}")
        app.stop()


if __name__ == "__main__":
    main()
