import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from .config import get_redis_client, MESSAGE_EXPIRY_SECONDS

logger = logging.getLogger(__name__)

class SessionRegistry:
    """
    Manages session metadata in Redis for automatic conversation analysis triggering.
    
    This class tracks active conversation sessions and their metadata, enabling
    the scheduler to identify sessions that need analysis before their Redis
    data expires.
    """
    
    SESSION_KEY_PREFIX = "session:"
    ANALYZED_KEY_PREFIX = "analyzed:"
    
    @classmethod
    async def register_session(
        cls, 
        user_id: str, 
        workflow_id: str, 
        agent_name: str
    ) -> bool:
        """
        Register a new conversation session in Redis.
        
        Args:
            user_id: The unique identifier for the user
            workflow_id: The unique identifier for the workflow/conversation
            agent_name: The name of the agent (general_agent, companion_agent)
            
        Returns:
            bool: True if session was registered successfully, False otherwise
        """
        if not all([user_id, workflow_id, agent_name]):
            logger.error("SessionRegistry: Invalid arguments - all parameters must be provided")
            return False
            
        try:
            redis = await get_redis_client()
            
            session_data = {
                "user_id": user_id,
                "workflow_id": workflow_id,
                "agent_name": agent_name,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "analyzed": False
            }
            
            session_key = f"{cls.SESSION_KEY_PREFIX}{workflow_id}"
            session_json = json.dumps(session_data)
            
            # Set with same expiry as message data
            result = await redis.setex(
                session_key,
                MESSAGE_EXPIRY_SECONDS,
                session_json
            )
            
            if result:
                logger.debug(f"Session registered: {workflow_id} for user: {user_id}, agent: {agent_name}")
            else:
                logger.warning(f"Failed to register session: {workflow_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error registering session {workflow_id}: {str(e)}")
            return False
    
    @classmethod
    async def get_session(cls, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session metadata from Redis.
        
        Args:
            workflow_id: The unique identifier for the workflow/conversation
            
        Returns:
            Optional[Dict]: Session metadata or None if not found
        """
        if not workflow_id:
            logger.error("SessionRegistry: Invalid workflow_id provided")
            return None
            
        try:
            redis = await get_redis_client()
            session_key = f"{cls.SESSION_KEY_PREFIX}{workflow_id}"
            
            session_json = await redis.get(session_key)
            if not session_json:
                logger.debug(f"No session found for workflow: {workflow_id}")
                return None
                
            session_data = json.loads(session_json)
            logger.debug(f"Retrieved session: {workflow_id}")
            return session_data
        except Exception as e:
            logger.error(f"Error retrieving session {workflow_id}: {str(e)}")
            return None
    
    @classmethod
    async def get_sessions_expiring_soon(cls, offset_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Get all sessions that will expire within the specified offset minutes.
        
        Args:
            offset_minutes: Minutes before expiry to consider as "expiring soon"
            
        Returns:
            List[Dict]: List of session metadata for sessions expiring soon
        """
        try:
            redis = await get_redis_client()
            expiring_sessions = []
            
            # Scan for all session keys
            async for key in redis.scan_iter(match=f"{cls.SESSION_KEY_PREFIX}*"):
                # Get TTL for each session key
                ttl_seconds = await redis.ttl(key)
                
                # Skip keys that don't exist or have no expiry
                if ttl_seconds <= 0:
                    continue
                    
                # Check if expiring within offset minutes
                offset_seconds = offset_minutes * 60
                if ttl_seconds <= offset_seconds:
                    # Get session data
                    session_json = await redis.get(key)
                    if session_json:
                        try:
                            session_data = json.loads(session_json)
                            session_data['ttl_seconds'] = ttl_seconds
                            expiring_sessions.append(session_data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON in session key {key}: {str(e)}")
                            continue
            
            logger.debug(f"Found {len(expiring_sessions)} sessions expiring within {offset_minutes} minutes")
            return expiring_sessions
            
        except Exception as e:
            logger.error(f"Error finding expiring sessions: {str(e)}")
            return []
    
    @classmethod
    async def mark_session_analyzed(cls, workflow_id: str) -> bool:
        """
        Mark a session as analyzed to prevent duplicate analysis.
        
        Args:
            workflow_id: The unique identifier for the workflow/conversation
            
        Returns:
            bool: True if marked successfully, False otherwise
        """
        if not workflow_id:
            logger.error("SessionRegistry: Invalid workflow_id provided")
            return False
            
        try:
            redis = await get_redis_client()
            
            # Update the session data to mark as analyzed
            session_key = f"{cls.SESSION_KEY_PREFIX}{workflow_id}"
            session_json = await redis.get(session_key)
            
            if not session_json:
                logger.warning(f"Session {workflow_id} not found for marking as analyzed")
                return False
                
            session_data = json.loads(session_json)
            session_data['analyzed'] = True
            session_data['analyzed_at'] = datetime.now(timezone.utc).isoformat()
            
            # Get current TTL to preserve it
            ttl = await redis.ttl(session_key)
            if ttl > 0:
                result = await redis.setex(
                    session_key,
                    ttl,
                    json.dumps(session_data)
                )
            else:
                result = await redis.set(session_key, json.dumps(session_data))
            
            if result:
                logger.debug(f"Session marked as analyzed: {workflow_id}")
            else:
                logger.warning(f"Failed to mark session as analyzed: {workflow_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error marking session {workflow_id} as analyzed: {str(e)}")
            return False
    
    @classmethod
    async def is_session_analyzed(cls, workflow_id: str) -> bool:
        """
        Check if a session has already been analyzed.
        
        Args:
            workflow_id: The unique identifier for the workflow/conversation
            
        Returns:
            bool: True if session has been analyzed, False otherwise
        """
        session_data = await cls.get_session(workflow_id)
        if not session_data:
            return False
            
        return session_data.get('analyzed', False)
    
    @classmethod
    async def cleanup_expired_sessions(cls) -> int:
        """
        Remove expired session entries from Redis.
        This is a maintenance function to clean up stale data.
        
        Returns:
            int: Number of expired sessions cleaned up
        """
        try:
            redis = await get_redis_client()
            cleaned_count = 0
            
            # Scan for all session keys
            async for key in redis.scan_iter(match=f"{cls.SESSION_KEY_PREFIX}*"):
                # Check if key exists (TTL check)
                ttl = await redis.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    cleaned_count += 1
            
            logger.debug(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
            return 0
