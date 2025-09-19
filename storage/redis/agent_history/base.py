import logging
from typing import List, Dict, ClassVar, Type, TypeVar, Any
from pydantic import BaseModel, Field
from .save_history import save_messages_to_redis
from .load_history import load_history

logger = logging.getLogger(__name__)

# Type variable for the class
T = TypeVar('T', bound='BaseAgentHistory')

class BaseAgentHistory(BaseModel):
    """
    Base class for all agent history models that stores messages in Redis.
    
    All agent history classes should inherit from this class to use Redis
    for message storage with automatic expiration.
    
    Attributes:
        messages: List of message dictionaries to be stored
        agent_type: Class variable that must be overridden by subclasses to specify agent type
    """
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="List of message dictionaries")
    agent_type: ClassVar[str] = ""  # Must be overridden by subclasses
    
    def __init_subclass__(cls, **kwargs):
        """Validate that subclasses set the agent_type class variable."""
        super().__init_subclass__(**kwargs)
        if not cls.agent_type:
            raise ValueError(f"Subclass {cls.__name__} must define a non-empty 'agent_type' class variable")
    
    @classmethod
    async def load_or_create(cls: Type[T], workflow_id: str) -> T:
        """
        Load messages from Redis or create a new instance if not found.
        
        Args:
            workflow_id: The unique identifier for the workflow
            
        Returns:
            An instance of the history class with loaded messages
            
        Raises:
            ValueError: If workflow_id is empty or invalid
        """
        if not workflow_id:
            logger.error(f"{cls.__name__}: Invalid workflow_id provided")
            raise ValueError("workflow_id must be provided")
            
        try:
            # Load from Redis
            logger.debug(f"Attempting to load {cls.__name__} for workflow: {workflow_id}")
            messages = await load_history(workflow_id, cls.agent_type)
            
            # If Redis has data, use it
            if messages:
                logger.debug(f"Loaded {len(messages)} messages for {cls.__name__}, workflow: {workflow_id}")
                return cls(messages=messages)
            
            # If not in Redis, create a new instance
            logger.debug(f"No existing {cls.__name__} found for workflow: {workflow_id}, creating new instance")
            return cls()
        except Exception as e:
            logger.error(f"Error loading {cls.__name__} for workflow {workflow_id}: {str(e)}")
            # Return empty instance on error to allow operation to continue
            return cls()
    
    async def save(self, workflow_id: str, user_id: str = None) -> bool:
        """
        Save messages to Redis with automatic expiration and session registration.
        
        Args:
            workflow_id: The unique identifier for the workflow
            user_id: The unique identifier for the user (optional, for session registration)
            
        Returns:
            bool: True if messages were saved successfully, False otherwise
            
        Raises:
            ValueError: If workflow_id is empty or invalid
        """
        if not workflow_id:
            logger.error(f"{self.__class__.__name__}: Invalid workflow_id provided for save operation")
            raise ValueError("workflow_id must be provided")
            
        try:
            # Convert messages to JSON-serializable format
            serializable_messages = []
            for msg in self.messages:
                serialized_msg = {}
                for key, value in msg.items():
                    if hasattr(value, 'model_dump'):
                        serialized_msg[key] = value.model_dump()
                    else:
                        serialized_msg[key] = value
                serializable_messages.append(serialized_msg)
            
            # Save to Redis (with expiry automatically set)
            logger.debug(f"Saving {len(serializable_messages)} messages for {self.__class__.__name__}, workflow: {workflow_id}")
            result = await save_messages_to_redis(workflow_id, self.__class__.agent_type, serializable_messages, user_id)
            
            if result:
                logger.debug(f"Successfully saved {self.__class__.__name__} for workflow: {workflow_id}")
            else:
                logger.warning(f"Failed to save {self.__class__.__name__} for workflow: {workflow_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error saving {self.__class__.__name__} for workflow {workflow_id}: {str(e)}")
            return False 