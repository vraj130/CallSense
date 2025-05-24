import asyncio
import websockets
import json
import logging
import re
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, task: str, llm: ChatOpenAI, use_vision: bool = False):
        self.task = task
        self.llm = llm
        self.use_vision = use_vision
        self.browser = None

    async def run(self, prompt: Optional[str] = None) -> Any:
        # Implementation will be added later
        pass

class VoiceBrowserAgent:
    def __init__(
        self, openai_api_key: str, stt_server_uri: str = "ws://localhost:8765"
    ):
        """
        Initialize the voice-controlled browser agent

        Args:
            openai_api_key: OpenAI API key for the language model
            stt_server_uri: URI of the STT WebSocket server
        """
        self.stt_uri = stt_server_uri
        self.websocket = None
        self.is_connected = False

        # Initialize browser-use agent
        self.llm = ChatOpenAI(
            model="gpt-4", api_key=openai_api_key, temperature=0.1
        )

        self.agent = Agent(
            task="Voice-controlled web browser assistant",
            llm=self.llm,
            use_vision=True,  # Enable vision for better understanding
        )

        # Command history for context
        self.command_history = []
        self.max_history = 10

    async def connect_to_stt(self):
        """Connect to the STT WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.stt_uri)
            self.is_connected = True
            logger.info(f"Connected to STT server at {self.stt_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to STT server: {e}")
            raise

    async def disconnect_from_stt(self):
        """Disconnect from STT server"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from STT server")

    def is_simple_command(self, text: str) -> bool:
        """Check if this is a simple command that doesn't need LLM processing"""
        simple_patterns = [
            r"^scroll (up|down)$",
            r"^refresh$",
            r"^reload$",
            r"^back$",
            r"^forward$",
            r"^click$",
            r"^stop$",
            r"^pause$",
        ]

        text_lower = text.lower().strip()
        return any(re.match(pattern, text_lower) for pattern in simple_patterns)

    def execute_simple_command(self, text: str) -> Optional[str]:
        """Execute simple commands without LLM"""
        text_lower = text.lower().strip()

        if text_lower == "scroll down":
            return "window.scrollBy(0, 500)"
        elif text_lower == "scroll up":
            return "window.scrollBy(0, -500)"
        elif text_lower in ["refresh", "reload"]:
            return "location.reload()"
        elif text_lower == "back":
            return "history.back()"
        elif text_lower == "forward":
            return "history.forward()"
        elif text_lower in ["stop", "pause"]:
            logger.info("Voice control paused")
            return None

        return None

    def build_context_prompt(self, voice_command: str) -> str:
        """Build a context-aware prompt for the LLM"""
        base_prompt = f"""
You are a voice-controlled web browser assistant. Execute the following voice command on the current webpage:

Voice Command: "{voice_command}"

Guidelines:
1. If the command is ambiguous, make the most reasonable interpretation
2. For navigation commands like "go to X", navigate to the appropriate URL
3. For interaction commands like "click X", find and click the most relevant element
4. For input commands like "type X" or "search for X", find input fields and enter the text
5. For commands like "find X" or "look for X", search the page or use search functionality
6. Be efficient and direct - complete the task in the fewest steps possible
7. If you need to scroll to find something, do so automatically

Recent command history for context:
{self._format_history()}

Execute this command now.
"""
        return base_prompt

    def _format_history(self) -> str:
        """Format recent command history"""
        if not self.command_history:
            return "No previous commands"

        history_str = ""
        for i, cmd in enumerate(self.command_history[-5:], 1):
            history_str += f"{i}. {cmd}\n"
        return history_str.strip()

    async def process_voice_command(
        self, voice_text: str, metadata: Dict[str, Any]
    ):
        """Process voice command and execute browser action"""
        voice_text = voice_text.strip()

        if not voice_text:
            return

        logger.info(f"Processing voice command: '{voice_text}'")

        # Add to history
        self.command_history.append(voice_text)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)

        try:
            # Check if it's a simple command first
            if self.is_simple_command(voice_text):
                js_command = self.execute_simple_command(voice_text)
                if js_command:
                    # Execute JavaScript directly for simple commands
                    await self.agent.browser.page.evaluate(js_command)
                    logger.info(f"Executed simple command: {voice_text}")
                return

            # For complex commands, use the LLM agent
            prompt = self.build_context_prompt(voice_text)

            # Execute the command using browser-use agent
            result = await self.agent.run(prompt)

            logger.info(f"Command executed successfully: {voice_text}")

            # Log the result if available
            if hasattr(result, "message") and result.message:
                logger.info(f"Agent response: {result.message}")

        except Exception as e:
            logger.error(f"Failed to execute command '{voice_text}': {e}")

            # Try to provide helpful feedback
            try:
                error_prompt = f"""
The previous command failed: "{voice_text}"
Error: {str(e)}

Please try an alternative approach to accomplish this task, or explain what went wrong.
"""
                await self.agent.run(error_prompt)
            except Exception as retry_error:
                logger.error(f"Recovery attempt also failed: {retry_error}")

    async def handle_stt_message(self, message: str):
        """Handle incoming STT WebSocket messages"""
        try:
            data = json.loads(message)

            if data.get("type") == "transcription":
                text = data.get("text", "").strip()
                if text:
                    await self.process_voice_command(text, data)

            elif data.get("type") == "error":
                logger.error(
                    f"STT Error: {data.get('message', 'Unknown error')}"
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse STT message: {e}")

    async def start_voice_control(
        self, initial_url: str = "https://www.google.com"
    ):
        """Start the voice-controlled browser session"""
        logger.info("Starting voice-controlled browser...")

        try:
            # Connect to STT server
            await self.connect_to_stt()

            # Navigate to initial URL
            logger.info(f"Navigating to {initial_url}")
            await self.agent.run(f"Navigate to {initial_url}")

            logger.info("Voice control active. Speak your commands!")
            logger.info("Example commands:")
            logger.info("  - 'Search for python tutorials'")
            logger.info("  - 'Click on the first result'")
            logger.info("  - 'Scroll down'")
            logger.info("  - 'Go to wikipedia.org'")
            logger.info("  - 'Type hello world'")

            # Listen for voice commands
            async for message in self.websocket:
                await self.handle_stt_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.info("STT connection closed")
        except KeyboardInterrupt:
            logger.info("Voice control stopped by user")
        except Exception as e:
            logger.error(f"Error in voice control: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")

        # Disconnect from STT server
        await self.disconnect_from_stt()

        # Close browser if it exists
        try:
            if hasattr(self.agent, "browser") and self.agent.browser:
                await self.agent.browser.close()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")


class VoiceBrowserSession:
    """High-level interface for voice browser sessions"""

    def __init__(
        self, openai_api_key: str, stt_server_uri: str = "ws://localhost:8765"
    ):
        self.voice_agent = VoiceBrowserAgent(openai_api_key, stt_server_uri)

    async def start_session(self, starting_url: str = "https://www.google.com"):
        """Start a new voice browser session"""
        await self.voice_agent.start_voice_control(starting_url)

    async def add_custom_command_handler(self, pattern: str, handler):
        """Add custom command patterns (for future extension)"""
        # This could be extended to allow custom command patterns
        pass


# Example usage and configuration
async def main():
    """Main function to run the voice browser"""

    # Configuration
    OPENAI_API_KEY = "your-openai-api-key-here"  # Replace with your key
    STT_SERVER_URI = "ws://localhost:8765"
    STARTING_URL = "https://www.google.com"

    # Validate API key
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
        logger.error("Please set your OpenAI API key!")
        logger.error(
            "Either set the OPENAI_API_KEY environment variable or modify the script"
        )
        return

    # Create and start the voice browser session
    session = VoiceBrowserSession(OPENAI_API_KEY, STT_SERVER_URI)

    try:
        await session.start_session(STARTING_URL)
    except KeyboardInterrupt:
        logger.info("Session terminated by user")
    except Exception as e:
        logger.error(f"Session error: {e}")


if __name__ == "__main__":
    # You can also set the API key via environment variable
    import os

    openai_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

    # Override the key in main if set via environment
    if openai_key != "your-openai-api-key-here":

        async def configured_main():
            session = VoiceBrowserSession(openai_key)
            await session.start_session()

        asyncio.run(configured_main())
    else:
        asyncio.run(main())
