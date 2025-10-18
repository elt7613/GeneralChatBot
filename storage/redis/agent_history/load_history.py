import json
import logging
from typing import Any, Dict, List
from .history_key_mapping import get_message_key
from ..config import get_redis_client, MESSAGE_EXPIRY_SECONDS

logger = logging.getLogger(__name__)

# Loading messages from Redis
async def load_history(workflow_id: str, agent_type: str) -> List[Dict[str, Any]]:
    """
    Loads messages from Redis.
    
    Args:
        workflow_id: The unique identifier for the workflow
        agent_type: The type of agent (e.g., 'worker_agent', 'sub_agent')
        
    Returns:
        List[Dict[str, Any]]: List of message dictionaries or empty list if not found or on error
    """
    if not workflow_id or not agent_type:
        logger.error("Invalid arguments: workflow_id and agent_type must be provided")
        return []
        
    key = await get_message_key(workflow_id, agent_type)
    
    try:
        # Get redis client
        redis = await get_redis_client()
        
        # Retrieve from Redis (async)
        messages_json = await redis.get(key)
        
        if not messages_json:
            logger.debug(f"No messages found for workflow: {workflow_id}, agent: {agent_type}")
            return []
            
        # Reset expiration time on access
        try:
            await redis.expire(key, MESSAGE_EXPIRY_SECONDS)
        except Exception as e:
            logger.warning(f"Failed to reset expiration for key {key}: {str(e)}")
            # Continue since the data was retrieved successfully
            
        # Parse JSON string to Python object
        messages = json.loads(messages_json)
        logger.debug(f"Successfully loaded {len(messages)} messages for workflow: {workflow_id}, agent: {agent_type}")
        return messages
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error for workflow {workflow_id}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Failed to load messages from Redis for workflow {workflow_id}: {str(e)}")
        return []
