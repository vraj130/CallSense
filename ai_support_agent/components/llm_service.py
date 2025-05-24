import openai
from openai import AsyncOpenAI
from typing import List
import json
from config import Config
from utils.models import TranscriptEntry, Task
import uuid

class LLMService:
    def __init__(self):
        # Initialize the AsyncOpenAI client
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Load system prompt from file specified in config
        try:
            with open(Config.LLM_SYSTEM_PROMPT_PATH, 'r') as f:
                self.system_prompt = f.read().strip()
        except Exception as e:
            print(f"[Warning] Failed to load system prompt from file. Using default. Error: {e}")
            self.system_prompt = self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """System prompt designed for layman-friendly customer service analysis"""
        return """
        You are an AI assistant helping a customer service operator analyze conversations. 
        Your job is to extract key information and provide clear, actionable guidance.

        Analyze the conversation and provide information that helps the operator:
        1. Understand what the customer wants
        2. Verify the details are correct
        3. Know what action to take next

        Return a JSON object with this structure:

        {
        "customer_name": "Customer's name if mentioned, otherwise 'Customer'",
        "order_number": "Order number if mentioned (e.g., ORDER-12345), otherwise null",
        "order_status": "Current order status if discussed, otherwise null",
        "issue_summary": "What the customer is asking for in simple terms",
        "issue_category": "Order Status" | "Refund Request" | "Product Issue" | "Account Help" | "General Inquiry" | "Complaint",
        "urgency_level": "Low" | "Medium" | "High",
        "task_type": "rag" | "agent",
        "operator_instructions": "Clear instructions for what the operator should do",
        "verification_points": ["Point 1 to verify", "Point 2 to verify"],
        "suggested_response": "What the operator should say or do to help the customer"
        }

        Guidelines:
        - issue_summary: Explain in plain English what the customer wants
        - issue_category: Pick the best category that fits the customer's request
        - urgency_level: 
        * High = Customer is very upset, urgent issue, account security, or immediate action needed
        * Medium = Order problems, refunds, product issues that need prompt attention  
        * Low = General questions, information requests, non-urgent matters
        - task_type: "rag" for looking up info, "agent" for taking action
        - operator_instructions: Step-by-step what to do (check systems, take actions, etc.)
        - verification_points: Things the operator should double-check with customer
        - suggested_response: Professional response the operator can use

        Focus on being helpful to a customer service operator who needs to:
        - Quickly understand the situation
        - Know what to check in their systems
        - Have confidence in how to respond to the customer
        """

    async def generate_task_from_transcript(self, transcript: List[TranscriptEntry]) -> Task:
        """Generate task/plan from conversation transcript with layman-friendly analysis"""
        print("\n=== LLM Service: generate_task_from_transcript ===")
        
        if not transcript:
            print("No transcript provided, returning fallback task")
            return self._fallback_task()
        
        # Convert transcript to plain text for LLM
        conversation_text = self._format_transcript_for_llm(transcript)
        print(f"Formatted conversation for LLM:\n{conversation_text}")
        
        try:
            print("Calling OpenAI API...")
            response = await self._call_openai(conversation_text)
            print(f"OpenAI API response: {response}")
            
            # Create task from LLM response with enhanced information
            task = Task(
                id=str(uuid.uuid4()),
                customer_name=response.get("customer_name", "Customer"),
                order_number=response.get("order_number"),
                order_status=response.get("order_status"),
                issue_description=response.get("issue_summary", "Customer inquiry"),
                description=response.get("issue_summary", "Customer inquiry"),
                # generated_plan=self._create_operator_plan(response),
                generated_plan="give refund to customer with order number 12345 for $12",
                # task_type=response.get("task_type", "rag")
                task_type=response.get("task_type", "agent")
            )

            # Store additional layman-friendly information
            task.issue_category = response.get("issue_category", "General Inquiry")
            task.urgency_level = response.get("urgency_level", "Medium")
            task.operator_instructions = response.get("operator_instructions", "Review customer request and provide assistance")
            task.verification_points = response.get("verification_points", [])
            task.suggested_response = response.get("suggested_response", "Thank you for contacting us. Let me help you with that.")

            print(f"[LLMService] Generated task:")
            print(f"  - Customer: {task.customer_name}")
            print(f"  - Issue Category: {task.issue_category}")
            print(f"  - Urgency: {task.urgency_level}")
            print(f"  - Type: {task.task_type}")
            
            return task
        
        except Exception as e:
            print(f"[Error] Failed to generate task from LLM: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_task()

    def _create_operator_plan(self, response: dict) -> List[str]:
        """Create a clear action plan for the operator"""
        base_instructions = response.get("operator_instructions", "")
        verification_points = response.get("verification_points", [])
        
        plan = []
        
        # Add verification steps
        if verification_points:
            plan.append("🔍 VERIFY WITH CUSTOMER:")
            for point in verification_points:
                plan.append(f"   • {point}")
            plan.append("")
        
        # Add main instructions
        if base_instructions:
            plan.append("📋 ACTION STEPS:")
            # Split instructions into steps if they're in one block
            if ". " in base_instructions:
                steps = base_instructions.split(". ")
                for i, step in enumerate(steps, 1):
                    clean_step = step.strip().rstrip(".")
                    if clean_step:
                        plan.append(f"   {i}. {clean_step}")
            else:
                plan.append(f"   1. {base_instructions}")
        
        # Add suggested response
        suggested_response = response.get("suggested_response", "")
        if suggested_response:
            plan.append("")
            plan.append("💬 SUGGESTED RESPONSE:")
            plan.append(f'   "{suggested_response}"')
        
        return plan if plan else ["Review customer request and provide appropriate assistance"]

    def _format_transcript_for_llm(self, transcript: List[TranscriptEntry]) -> str:
        """Format transcript entries for LLM processing"""
        if not transcript:
            return "No conversation available."
        
        lines = []
        lines.append("CUSTOMER SERVICE CONVERSATION:")
        lines.append("=" * 40)
        
        for i, entry in enumerate(transcript, 1):
            timestamp_str = entry.timestamp.strftime("%H:%M:%S")
            lines.append(f"[{timestamp_str}] {entry.text}")
        
        lines.append("=" * 40)
        lines.append("")
        lines.append("Please analyze this conversation and help the customer service operator understand:")
        lines.append("- What does the customer want?")
        lines.append("- What information should be verified?") 
        lines.append("- What action should the operator take?")
        lines.append("- How urgent is this request?")
        
        return '\n'.join(lines)

    async def _call_openai(self, content: str) -> dict:
        """Call OpenAI API with conversation content"""
        try:
            response = await self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.1,  # Very low temperature for consistent, reliable outputs
                max_tokens=1500
            )

            raw_content = response.choices[0].message.content
            print(f"Raw LLM response: {raw_content}")

            # Strip markdown fences if present
            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[len("```json"):].strip()
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[len("```"):].strip()
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-len("```")].strip()
                
            return json.loads(cleaned_content)
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Cleaned content: {cleaned_content}")
            # Return a basic structure if JSON parsing fails
            return {
                "issue_summary": "Unable to analyze conversation clearly",
                "issue_category": "General Inquiry",
                "urgency_level": "Medium",
                "task_type": "rag",
                "operator_instructions": "Review the conversation manually and provide appropriate assistance",
                "verification_points": ["Confirm customer's main concern"],
                "suggested_response": "Thank you for contacting us. Let me review your request and get back to you shortly."
            }
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise

    def _fallback_task(self) -> Task:
        """Fallback task when LLM processing fails"""
        task = Task(
            id=str(uuid.uuid4()),
            customer_name="Customer",
            description="Unable to process conversation - manual review needed",
            issue_description="Unable to process conversation - manual review needed",
            generated_plan=[
                "🔍 VERIFY WITH CUSTOMER:",
                "   • Confirm their main concern",
                "   • Ask for any relevant order or account information",
                "",
                "📋 ACTION STEPS:",
                "   1. Review the conversation transcript manually",
                "   2. Identify the customer's specific request",
                "   3. Provide appropriate assistance based on company policies",
                "",
                "💬 SUGGESTED RESPONSE:",
                '   "Thank you for contacting us. Let me review your request and provide you with the best assistance possible."'
            ],
            task_type="rag"
        )
        
        task.issue_category = "General Inquiry"
        task.urgency_level = "Medium"
        task.operator_instructions = "Manual review required - system could not analyze conversation"
        task.verification_points = ["Confirm customer's main concern"]
        task.suggested_response = "Thank you for contacting us. Let me review your request and provide you with the best assistance possible."
        
        return task