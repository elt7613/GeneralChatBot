import json
import logging
from typing import Any, Dict, List
from .history_key_mapping import get_message_key
from ..config import get_redis_client, MESSAGE_EXPIRY_SECONDS

logger = logging.getLogger(__name__)

# Saving messages to Redis
async def save_messages_to_redis(
    workflow_id: str, 
    agent_type: str, 
    messages: Any
) -> bool:
    """
    Saves messages to Redis with expiration time.
    
    Args:
        workflow_id: The unique identifier for the workflow
        agent_type: The type of agent (e.g., 'worker_agent', 'sub_agent')
        messages: List of message dictionaries to store
        
    Returns:
        bool: True if messages were saved successfully, False otherwise
    """
    if not workflow_id or not agent_type:
        logger.error("Invalid arguments: workflow_id and agent_type must be provided")
        return False
        
    if not messages:
        logger.warning(f"Empty messages list for workflow: {workflow_id}, agent: {agent_type}")
        return True  # Nothing to save, but not an error
    
    key = await get_message_key(workflow_id, agent_type)
    
    try:
        # Get redis client
        redis = await get_redis_client()
        
        # Serialize messages to JSON string
        messages_json = json.dumps(messages)
        
        # Use async Redis client
        result = await redis.setex(
            key,
            MESSAGE_EXPIRY_SECONDS,
            messages_json
        )
        return result  # Redis returns True if successful
    except json.JSONDecodeError as e:
        logger.error(f"JSON serialization error for workflow {workflow_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to save messages to Redis for workflow {workflow_id}: {str(e)}")
        return False
