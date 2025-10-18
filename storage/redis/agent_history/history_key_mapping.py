import logging

logger = logging.getLogger(__name__)

# Key naming conventions
async def get_message_key(workflow_id: str, agent_type: str) -> str:
    """
    Generates a Redis key for storing messages for a specific workflow and agent.
    
    Args:
        workflow_id: The unique identifier for the workflow
        agent_type: The type of agent (e.g., 'worker_agent', 'sub_agent')
        
    Returns:
        str: Formatted Redis key in the pattern "workflow:{workflow_id}:messages:{agent_type}"
    """
    return f"workflow:{workflow_id}:messages:{agent_type}"