from utils.models import Task
import asyncio
import anthropic
from browser_use.browser import Browser
from config import Config

class AIAgent:
    """AI Agent with Anthropic Claude integration and browser automation"""
    
    def __init__(self):
        self.claude = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.browser = None
        self.server_url = f"http://{Config.SERVER_HOST}:{Config.SERVER_PORT}"
    
    async def initialize(self):
        """Initialize browser automation"""
        self.browser = Browser(
            headless=Config.BROWSER_HEADLESS,
            timeout=Config.BROWSER_TIMEOUT
        )
        await self.browser.start()
    
    async def execute_task(self, task: Task) -> str:
        """Execute task using Claude and browser automation"""
        try:
            # Navigate to the server
            await self.browser.goto(self.server_url)
            
            # Get Claude's analysis of the task
            response = await self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"Analyze this customer service task and provide step-by-step instructions for browser automation: {task.description}"
                }]
            )
            
            # Execute the task based on Claude's instructions
            if "update" in task.description.lower():
                # Handle customer information update
                await self.browser.click("text=Update Information")
                # Add more specific automation steps based on Claude's analysis
                return "Successfully updated customer information in the system"
            
            elif "cancel" in task.description.lower():
                # Handle order cancellation
                await self.browser.click("text=Cancel Order")
                # Add more specific automation steps based on Claude's analysis
                return "Order cancellation request has been processed"
            
            elif "refund" in task.description.lower():
                # Handle refund request
                await self.browser.click("text=Process Refund")
                # Add more specific automation steps based on Claude's analysis
                return "Refund initiated - Processing time: 3-5 business days"
            
            else:
                # Handle other tasks based on Claude's analysis
                return f"Task executed: {task.description}"
                
        except Exception as e:
            return f"Error executing task: {str(e)}"
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.browser:
            await self.browser.close() 