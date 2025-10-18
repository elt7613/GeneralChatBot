import redis.asyncio as redis
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL")
MESSAGE_EXPIRY_SECONDS = int(os.environ.get("MESSAGE_EXPIRY_SECONDS"))

# Automatic Conversation Analyzer Trigger Settings
TRIGGER_OFFSET_MINUTES = int(os.environ.get("TRIGGER_OFFSET_MINUTES"))
SCHEDULER_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_INTERVAL_SECONDS"))

# Global redis client
redis_client = None

async def get_redis_client():
    """Get or create the Redis client."""
    global redis_client
    if redis_client is None:
        try:
            # Create async Redis client using redis.asyncio
            redis_client = redis.from_url(
                REDIS_URL,
                max_connections=20,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                health_check_interval=30,
                retry_on_timeout=True
            )
            logger.info("Redis client created successfully")
        except Exception as e:
            logger.error(f"Failed to create Redis client: {str(e)}")
            raise
    return redis_client

# Initialize the client at module load time
async def init_redis():
    """Initialize Redis client. Call this at application startup."""
    await get_redis_client()
