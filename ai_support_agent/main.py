import asyncio
import threading
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
            self.rag_service, 
            self.ai_agent, 
            self.state_manager
        )
        self.frontend = GradioInterface(self.state_manager)
        self.transcription_task = None
        self.background_loop = None
        self.background_thread = None

    async def initialize(self):
        """Initialize all services"""
        await self.rag_service.initialize()
        await self.ai_agent.initialize()
        print("All services initialized")
    
    async def _transcription_loop(self):
        """Background task for transcription"""
        print("\n=== Starting transcription loop ===")
        try:
            async for entry in self.speech_service.start_transcription():
                print(f"\nReceived entry: {entry.speaker.value}: {entry.text}")
                await self.state_manager.add_transcript_entry(entry)
                print("Entry added to state manager")
        except Exception as e:
            print(f"Error in transcription loop: {str(e)}")
            raise
    
    def run_background_loop(self):
        self.background_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.background_loop)
        self.background_loop.run_until_complete(self.initialize())
        self.background_loop.run_until_complete(self._transcription_loop())

    def start_background_services(self):
        self.background_thread = threading.Thread(target=self.run_background_loop, daemon=True)
        self.background_thread.start()
        print("Background services started")

    def process_trigger_sync(self):
        print("\n=== Processing trigger ===")
        transcript = self.state_manager.get_state().transcript
        print(f"Current transcript length: {len(transcript)}")
        if not transcript:
            print("No transcript found")
            return "No conversation to process", ""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
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
            loop.close()
            return "Task completed successfully", result
        except Exception as e:
            print(f"Error in process_trigger_sync: {str(e)}")
            return f"Error: {str(e)}", ""

    def run(self):
        self.start_background_services()
        interface = self.frontend.create_interface(
            trigger_callback=self.process_trigger_sync
        )
        interface.launch(
            server_port=Config.GRADIO_PORT,
            share=False,
            inbrowser=True
        )

def main():
    """Entry point"""
    app = CustomerSupportAIApp()
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        if app.speech_service:
            app.speech_service.stop_transcription()

if __name__ == "__main__":
    main()
