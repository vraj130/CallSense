from utils.models import Task
from .rag_service import RAGService
from .ai_agent import AIAgent
from .state_manager import StateManager

class Orchestrator:
    def __init__(self, rag_service: RAGService, ai_agent: AIAgent, state_manager: StateManager):
        self.rag_service = rag_service
        self.ai_agent = ai_agent
        self.state_manager = state_manager
        self.llm_service = None  # Can add LLM-based routing logic later
    
    async def route_task(self, task: Task) -> str:
        """Route task to appropriate service based on task type"""
        
        # Update task status
        task.status = "processing"
        await self.state_manager.update_task(task)
        
        try:
            if task.task_type == "rag":
                result = await self.rag_service.search(task.description)
            elif task.task_type == "agent":
                result = await self.ai_agent.execute_task(task)
            else:
                result = "Unknown task type"
            
            # Update task with result
            task.status = "completed"
            task.result = result
            await self.state_manager.update_task(task)
            
            return result
            
        except Exception as e:
            task.status = "failed"
            task.result = f"Error: {str(e)}"
            await self.state_manager.update_task(task)
            raise 