import gradio as gr
from typing import List, Tuple, Callable, Optional
from components.state_manager import StateManager
from utils.models import AppState, Speaker

class GradioInterface:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.interface = None
        self.trigger_callback = None
        
    def create_interface(self, trigger_callback: Optional[Callable] = None):
        """Create Gradio interface"""
        self.trigger_callback = trigger_callback
        with gr.Blocks(title="Customer Support AI Assistant") as self.interface:
            gr.Markdown("# Customer Support AI Assistant")
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Conversation display
                    conversation_display = gr.Chatbot(
                        label="Ongoing Conversation",
                        height=400
                    )
                    
                    # Trigger button
                    trigger_btn = gr.Button(
                        "🤖 Generate AI Assistance", 
                        variant="primary"
                    )
                
                with gr.Column(scale=1):
                    # Status display
                    status_display = gr.Textbox(
                        label="System Status",
                        lines=5,
                        interactive=False
                    )
                    
                    # Task result display
                    result_display = gr.Textbox(
                        label="AI Assistant Response",
                        lines=10,
                        interactive=False
                    )
                    
                    # Confirmation section
                    with gr.Row():
                        confirm_btn = gr.Button("✅ Execute", variant="primary")
                        reject_btn = gr.Button("❌ Cancel", variant="stop")
            
            # Hidden state component
            state_component = gr.State(value={"conversation": [], "status": "Ready"})
            
            # Set up event handlers
            trigger_btn.click(
                fn=self.handle_trigger,
                inputs=[state_component],
                outputs=[status_display, result_display, state_component]
            )
            
            # Auto-refresh conversation
            self.interface.load(
                fn=self.update_conversation,
                outputs=[conversation_display, state_component],
                every=1  # Update every second
            )
        
        return self.interface
    
    def update_conversation(self) -> Tuple[List[Tuple[str, str]], dict]:
        """Update conversation display from state"""
        state = self.state_manager.get_state()
        
        # Format conversation for Gradio chatbot
        conversation = []
        for entry in state.transcript:
            if entry.speaker == Speaker.CUSTOMER:
                conversation.append((entry.text, None))
            else:
                conversation.append((None, entry.text))
        
        state_dict = {
            "conversation": conversation,
            "status": f"Task: {state.current_task.status if state.current_task else 'No active task'}"
        }
        
        return conversation, state_dict
    
    async def handle_trigger(self, state_dict: dict) -> Tuple[str, str, dict]:
        """Handle trigger button click"""
        # This will be connected to the main app logic
        status = "Processing transcript with AI..."
        result = "AI analysis will appear here"
        
        # Update status
        current_state = self.state_manager.get_state()
        if current_state.current_task:
            status = f"Task Status: {current_state.current_task.status}\nTask: {current_state.current_task.description}"
            if current_state.current_task.result:
                result = current_state.current_task.result
        
        return status, result, state_dict
    
    def launch(self, **kwargs):
        """Launch Gradio interface"""
        if self.interface is None:
            self.create_interface()
        return self.interface.launch(**kwargs) 