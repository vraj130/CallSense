import gradio as gr
from typing import List, Tuple, Callable, Optional
from components.state_manager import StateManager
from utils.models import AppState, Speaker
import asyncio
import threading


class GradioInterface:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.interface = None
        self.trigger_callback = None
        self.conversation_display = None
        self.status_display = None
        self.result_display = None
        self.state_component = None

    def create_interface(self, trigger_callback: Optional[Callable] = None):
        """Create Gradio interface"""
        self.trigger_callback = trigger_callback
        with gr.Blocks(
            title="Customer Support AI Assistant", theme=gr.themes.Soft()
        ) as self.interface:
            gr.Markdown("# 🤖 Customer Support AI Assistant")
            gr.Markdown(
                "*Real-time speech transcription and AI-powered assistance*"
            )

            with gr.Row():
                with gr.Column(scale=2):
                    # Conversation display
                    self.conversation_display = gr.Chatbot(
                        label="📞 Live Conversation",
                        height=400,
                        show_label=True,
                        elem_id="conversation",
                        avatar_images=("🗣️", "🎧"),  # Customer and Agent avatars
                    )

                    # Control buttons
                    with gr.Row():
                        trigger_btn = gr.Button(
                            "🤖 Generate AI Assistance",
                            variant="primary",
                            size="lg",
                        )
                        clear_btn = gr.Button(
                            "🗑️ Clear Conversation", variant="secondary"
                        )
                        save_btn = gr.Button(
                            "💾 Save Transcript", variant="secondary"
                        )

                    # Debug info
                    debug_info = gr.Textbox(
                        label="📊 System Status",
                        lines=2,
                        interactive=False,
                        show_label=True,
                    )

                with gr.Column(scale=1):
                    # Task analysis display
                    self.status_display = gr.Textbox(
                        label="🔍 Task Analysis",
                        lines=8,
                        interactive=False,
                        show_label=True,
                    )

                    # AI response display
                    self.result_display = gr.Textbox(
                        label="🎯 AI Assistant Response",
                        lines=12,
                        interactive=False,
                        show_label=True,
                    )

                    # Action buttons
                    with gr.Row():
                        confirm_btn = gr.Button(
                            "✅ Execute Action", variant="primary"
                        )
                        reject_btn = gr.Button("❌ Cancel", variant="stop")

            # Hidden state component
            self.state_component = gr.State(
                value={"conversation": [], "status": "Ready"}
            )

            # Set up event handlers
            trigger_btn.click(
                fn=self.handle_trigger,
                inputs=[self.state_component],
                outputs=[
                    self.status_display,
                    self.result_display,
                    self.state_component,
                ],
            )

            clear_btn.click(
                fn=self.handle_clear,
                outputs=[
                    self.conversation_display,
                    self.status_display,
                    self.result_display,
                    debug_info,
                    self.state_component,
                ],
            )

            save_btn.click(fn=self.handle_save, outputs=[debug_info])

            # Auto-refresh conversation
            self.interface.load(
                fn=self.update_conversation,
                outputs=[
                    self.conversation_display,
                    self.state_component,
                    debug_info,
                ],
                every=1.0,  # Update every 1 second
            )

        return self.interface

    def update_conversation(self) -> Tuple[List[Tuple[str, str]], dict, str]:
        """Update conversation display from state"""
        try:
            state = self.state_manager.get_state()

            # Debug info
            debug_text = f"📊 Entries: {len(state.transcript)} | Conversation ID: {state.conversation_id[:8]}..."
            if state.current_task:
                debug_text += f" | Task: {state.current_task.status}"

            # Format conversation for Gradio chatbot
            conversation = []
            for entry in state.transcript:
                if entry.speaker == Speaker.CUSTOMER:
                    conversation.append((entry.text, None))
                elif entry.speaker == Speaker.AGENT:
                    conversation.append((None, entry.text))
                else:
                    # For any other speaker, show as system message
                    conversation.append(
                        (f"[{entry.speaker.value}] {entry.text}", None)
                    )

            state_dict = {
                "conversation": conversation,
                "status": f"Active - {len(state.transcript)} messages",
                "task_status": (
                    state.current_task.status
                    if state.current_task
                    else "No active task"
                ),
            }

            # print(f"UI Update - Conversation items: {len(conversation)}")  # Debug print
            return conversation, state_dict, debug_text

        except Exception as e:
            error_msg = f"❌ Error updating: {str(e)}"
            print(error_msg)
            return [], {"conversation": [], "status": "Error"}, error_msg

    def handle_trigger(self, state_dict: dict) -> Tuple[str, str, dict]:
        """Handle Generate AI Assistance button"""
        print("\n=== Generate AI Assistance button clicked ===")

        if self.trigger_callback:
            try:
                status, result = self.trigger_callback()
                return status, result, state_dict
            except Exception as e:
                print(f"Error in trigger callback: {str(e)}")
                error_msg = f"❌ Error: {str(e)}"
                return (
                    error_msg,
                    "Please try again or check the system logs.",
                    state_dict,
                )
        else:
            # Fallback response
            current_state = self.state_manager.get_state()
            if current_state.transcript:
                status = f"📋 Ready to process {len(current_state.transcript)} transcript entries"
                result = "Click 'Generate AI Assistance' to analyze the conversation and get AI recommendations."
            else:
                status = "⚠️ No conversation to process"
                result = "Please have a conversation first before generating AI assistance."

            return status, result, state_dict

    def handle_clear(self) -> Tuple[List, str, str, str, dict]:
        """Handle Clear Conversation button"""
        print("=== Clear conversation clicked ===")
        try:
            self.state_manager.clear_transcript()
            empty_state = {
                "conversation": [],
                "status": "Conversation cleared",
                "task_status": "Ready for new conversation",
            }
            return (
                [],  # Empty conversation
                "🗑️ Conversation cleared",  # Status display
                "Ready for new conversation",  # Result display
                "🔄 New conversation started",  # Debug info
                empty_state,  # State component
            )
        except Exception as e:
            error_msg = f"❌ Error clearing: {str(e)}"
            return (
                [],
                error_msg,
                "",
                error_msg,
                {"conversation": [], "status": "Error"},
            )

    def handle_save(self) -> str:
        """Handle Save Transcript button"""
        print("=== Save transcript clicked ===")
        try:
            import asyncio

            # Create new event loop for sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                filename = loop.run_until_complete(
                    self.state_manager.save_current_transcript()
                )
                if filename:
                    return f"💾 Transcript saved successfully to: {filename}"
                else:
                    return "⚠️ No transcript to save or storage not configured"
            finally:
                loop.close()

        except Exception as e:
            error_msg = f"❌ Error saving transcript: {str(e)}"
            print(error_msg)
            return error_msg

    def launch(self, **kwargs):
        """Launch Gradio interface"""
        if self.interface is None:
            self.create_interface()
        return self.interface.launch(**kwargs)
