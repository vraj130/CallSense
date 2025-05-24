import asyncio
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
        
        # Background tasks
        self.transcription_task = None
    
    async def initialize(self):
        """Initialize all services"""
        await self.rag_service.initialize()
        await self.ai_agent.initialize()
        print("All services initialized")
    
    async def start_transcription(self):
        """Start speech-to-text transcription"""
        print("\n=== Creating transcription task ===")
        self.transcription_task = asyncio.create_task(self._transcription_loop())
        print("Transcription task created")
        # Don't await here - we want the task to run in the background
        # The task will be cleaned up when the application exits
    
    async def _transcription_loop(self):
        """Background task for transcription"""
        print("\n=== Starting transcription loop ===")
        try:
            async for entry in self.speech_service.start_transcription():
                print(f"\nReceived entry from speech service: {entry.speaker.value}: {entry.text}")
                await self.state_manager.add_transcript_entry(entry)
                print("Entry added to state manager")
        except Exception as e:
            print(f"Error in transcription loop: {str(e)}")
            raise
    
    async def process_trigger(self):
        """Process frontend trigger to generate and execute AI task"""
        print("\n=== Starting process_trigger ===")
        # Get current transcript
        transcript = await self.state_manager.get_transcript()
        print(f"Current transcript length: {len(transcript)}")
        
        if not transcript:
            print("No transcript found")
            return "No conversation to process"
        
        print("Generating task from transcript...")
        # Generate task from transcript
        task = await self.llm_service.generate_task_from_transcript(transcript)
        print(f"Generated task: {task.description}")
        
        print("Routing task...")
        # Route and execute task
        result = await self.orchestrator.route_task(task)
        print(f"Task result: {result}")
        
        return result
    
    def setup_frontend_handlers(self):
        """Connect frontend handlers to backend logic"""
        # Override the trigger handler in frontend
        original_handle_trigger = self.frontend.handle_trigger
        
        async def enhanced_handle_trigger(state_dict):
            print("\n=== Button clicked - enhanced_handle_trigger ===")
            try:
                # Process the trigger
                result = await self.process_trigger()
                print("Process trigger completed")
                # Then call original handler to update UI
                return await original_handle_trigger(state_dict)
            except Exception as e:
                print(f"Error in enhanced_handle_trigger: {str(e)}")
                return f"Error: {str(e)}", "", state_dict
        
        self.frontend.handle_trigger = enhanced_handle_trigger
    
    async def run(self):
        """Main application loop"""
        # Initialize services
        await self.initialize()
        
        # Start transcription
        print("\n=== Starting transcription service ===")
        await self.start_transcription()
        print("Transcription service started")
        
        # Setup frontend handlers
        self.setup_frontend_handlers()
        
        # Launch Gradio interface in a separate thread
        print("\n=== Launching Gradio interface ===")
        
        import threading
        def run_gradio():
            self.frontend.launch(
                server_port=Config.GRADIO_PORT,
                share=False,
                inbrowser=True
            )
        
        # Start Gradio in a daemon thread
        gradio_thread = threading.Thread(target=run_gradio, daemon=True)
        gradio_thread.start()
        
        print("Gradio started in separate thread")
        
        # Keep the main event loop running for transcription and other async tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            if self.speech_service:
                self.speech_service.stop_transcription()

def main():
    """Entry point"""
    app = CustomerSupportAIApp()
    
    # Run the application
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nShutting down...")
        if app.speech_service:
            app.speech_service.stop_transcription()

if __name__ == "__main__":
    main()
