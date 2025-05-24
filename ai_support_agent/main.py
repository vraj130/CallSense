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
        self.transcription_task = asyncio.create_task(self._transcription_loop())
    
    async def _transcription_loop(self):
        """Background task for transcription"""
        async for entry in self.speech_service.start_transcription():
            await self.state_manager.add_transcript_entry(entry)
    
    async def process_trigger(self):
        """Process frontend trigger to generate and execute AI task"""
        # Get current transcript
        transcript = await self.state_manager.get_transcript()
        
        if not transcript:
            return "No conversation to process"
        
        # Generate task from transcript
        task = await self.llm_service.generate_task_from_transcript(transcript)
        
        # Route and execute task
        result = await self.orchestrator.route_task(task)
        
        return result
    
    def setup_frontend_handlers(self):
        """Connect frontend handlers to backend logic"""
        # Override the trigger handler in frontend
        original_handle_trigger = self.frontend.handle_trigger
        
        async def enhanced_handle_trigger(state_dict):
            try:
                # Process the trigger
                await self.process_trigger()
                # Then call original handler to update UI
                return await original_handle_trigger(state_dict)
            except Exception as e:
                return f"Error: {str(e)}", "", state_dict
        
        self.frontend.handle_trigger = enhanced_handle_trigger
    
    async def run(self):
        """Main application loop"""
        # Initialize services
        await self.initialize()
        
        # Start transcription
        await self.start_transcription()
        
        # Setup frontend handlers
        self.setup_frontend_handlers()
        
        # Launch Gradio interface (this blocks)
        self.frontend.launch(
            server_port=Config.GRADIO_PORT,
            share=False,
            inbrowser=True
        )

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
