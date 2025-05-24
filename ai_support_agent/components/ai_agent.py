from utils.models import Task
import asyncio
import anthropic
from browser_use import Agent
from config import Config
import json
from datetime import datetime

class AIAgent:
    """AI Agent with Anthropic Claude integration and browser automation"""
    
    def __init__(self):
        print("\n=== Initializing AIAgent ===")
        self.claude = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.agent = None
        self.server_url = f"http://{Config.SERVER_HOST}:{Config.SERVER_PORT}"
        self.start_time = None
        print(f"Server URL: {self.server_url}")
    
    async def initialize(self):
        """Initialize browser automation agent"""
        self.start_time = datetime.now()
        print(f"\n=== Starting browser automation at {self.start_time} ===")
        
        try:
            self.agent = Agent(
                task="""Navigate to the Gradio customer service portal and handle customer requests.
                The interface has the following elements:
                - Tabs for different actions (Cancel Order, Price Match, Refund)
                - Text inputs for Order ID and other information
                - Number inputs for amounts
                - Buttons to process actions
                - Result display areas
                
                When interacting:
                1. First click the appropriate tab for the action
                2. Fill in the required fields
                3. Click the process button
                4. Wait for and read the result
                
                Take your time with each action and make sure to:
                - Wait for elements to be visible before interacting
                - Verify the correct tab is selected
                - Double-check input values before submitting
                - Wait for results to appear before proceeding
                """,
                llm=self.claude
            )
            print("✓ Browser automation agent initialized")
        except Exception as e:
            print(f"❌ Failed to initialize browser: {str(e)}")
            raise
    
    async def execute_task(self, task: Task) -> str:
        """Execute task using Claude and browser automation"""
        task_start_time = datetime.now()
        print(f"\n=== Starting task at {task_start_time} ===")
        print(f"Task: {task.description}")
        
        try:
            # Update the agent's task with the specific customer request
            self.agent.task = f"""Navigate to {self.server_url} and handle this customer request: {task.description}
            
            Remember to:
            1. Click the correct tab first
            2. Fill in all required fields
            3. Click the process button
            4. Read and return the result message
            
            The interface is built with Gradio, so look for:
            - Tab elements with text like 'Cancel Order', 'Price Match', or 'Refund'
            - Text inputs with labels like 'Order ID', 'Customer Name'
            - Number inputs for amounts
            - Buttons with text like 'Process Refund', 'Cancel Order', etc.
            - Result messages in HTML format
            
            Take your time with each step and make sure to:
            - Wait for elements to be visible before interacting
            - Verify the correct tab is selected
            - Double-check input values before submitting
            - Wait for results to appear before proceeding
            """
            
            print("Starting browser automation...")
            self.agent.task = task_instructions
            
            # Run the agent to handle the task
            result = await self.agent.run()
            print("✓ Browser automation completed")
            print(f"Raw result: {result}")
            
            # Get Claude's analysis of the result
            print("Analyzing results with Claude...")
            response = await self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze the browser automation result and provide a customer-friendly response.
                    The result contains HTML formatting, so extract the meaningful information and present it clearly:
                    {result}"""
                }]
            )
            
            task_end_time = datetime.now()
            duration = (task_end_time - task_start_time).total_seconds()
            print(f"✓ Task completed in {duration:.2f} seconds")
            print(f"Claude's response: {response.content[0].text}")
            
            return response.content[0].text
                
        except Exception as e:
            print(f"❌ Error executing task: {str(e)}")
            return f"Error executing task: {str(e)}"
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.agent:
            print("\n=== Cleaning up resources ===")
            try:
                await self.agent.close()
                print("✓ Browser closed successfully")
                if self.start_time:
                    total_duration = (datetime.now() - self.start_time).total_seconds()
                    print(f"Total runtime: {total_duration:.2f} seconds")
            except Exception as e:
                print(f"❌ Error during cleanup: {str(e)}") 