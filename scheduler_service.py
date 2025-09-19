"""
Scheduler Service Integration Module

This module provides easy integration of the automatic conversation analyzer 
scheduler with your main application. Import and use these functions to 
start/stop the background scheduler that triggers conversation analysis 
before Redis data expires.

Usage:
    from scheduler_service import start_conversation_scheduler, stop_conversation_scheduler
    
    # At application startup
    await start_conversation_scheduler()
    
    # At application shutdown
    await stop_conversation_scheduler()
"""

import logging
import asyncio
from typing import Optional

from storage.redis.scheduler.conversation_scheduler import (
    start_scheduler, 
    stop_scheduler, 
    get_scheduler
)

logger = logging.getLogger(__name__)

class SchedulerServiceManager:
    """
    Manager class for the conversation analyzer scheduler service.
    Provides lifecycle management and status monitoring.
    """
    
    def __init__(self):
        self.is_started = False
        self._startup_task: Optional[asyncio.Task] = None
    
    async def start(self, graph_factory=None) -> bool:
        """
        Start the conversation analyzer scheduler service.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_started:
            logger.warning("SchedulerServiceManager: Service already started")
            return True
            
        try:
            logger.info("Starting Conversation Analyzer Scheduler Service...")
            
            # Start the scheduler
            success = await start_scheduler(graph_factory)
            
            if success:
                self.is_started = True
                logger.info("✅ Conversation Analyzer Scheduler Service started successfully")
                logger.info("🔍 Automatic conversation analysis enabled - sessions will be analyzed 5 minutes before Redis expiry")
            else:
                logger.error("❌ Failed to start Conversation Analyzer Scheduler Service")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error starting Conversation Analyzer Scheduler Service: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the conversation analyzer scheduler service.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_started:
            logger.warning("SchedulerServiceManager: Service not started")
            return True
            
        try:
            logger.info("Stopping Conversation Analyzer Scheduler Service...")
            
            # Stop the scheduler
            success = await stop_scheduler()
            
            if success:
                self.is_started = False
                logger.info("✅ Conversation Analyzer Scheduler Service stopped successfully")
            else:
                logger.error("❌ Failed to stop Conversation Analyzer Scheduler Service")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error stopping Conversation Analyzer Scheduler Service: {str(e)}")
            return False
    
    async def get_status(self) -> dict:
        """
        Get the current status of the scheduler service.
        
        Returns:
            dict: Status information
        """
        try:
            scheduler = await get_scheduler()
            status = scheduler.get_status()
            status['service_manager_started'] = self.is_started
            return status
        except Exception as e:
            return {
                'error': str(e),
                'service_manager_started': self.is_started,
                'is_running': False,
                'scheduler_healthy': False,
                'trigger_service_healthy': False
            }
    
    async def run_manual_check(self) -> dict:
        """
        Manually trigger a check for expiring sessions (useful for testing).
        
        Returns:
            dict: Results of the manual check
        """
        try:
            scheduler = await get_scheduler()
            return await scheduler.run_manual_check()
        except Exception as e:
            logger.error(f"Error during manual check: {str(e)}")
            return {'error': str(e)}
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired session entries (maintenance function).
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            scheduler = await get_scheduler()
            return await scheduler.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
            return 0

# Global service manager instance
_service_manager: Optional[SchedulerServiceManager] = None

def get_service_manager() -> SchedulerServiceManager:
    """Get or create the global service manager instance."""
    global _service_manager
    if _service_manager is None:
        _service_manager = SchedulerServiceManager()
    return _service_manager

async def start_conversation_scheduler(graph_factory=None) -> bool:
    """
    Start the automatic conversation analyzer scheduler service.
    
    Call this function at your application startup to enable automatic
    conversation analysis before Redis data expires.
    
    Args:
        graph_factory: Factory function that returns a compiled LangGraph instance
    
    Returns:
        bool: True if started successfully, False otherwise
    """
    manager = get_service_manager()
    return await manager.start(graph_factory)

async def stop_conversation_scheduler() -> bool:
    """
    Stop the automatic conversation analyzer scheduler service.
    
    Call this function at your application shutdown for graceful cleanup.
    
    Returns:
        bool: True if stopped successfully, False otherwise
    """
    manager = get_service_manager()
    return await manager.stop()

async def get_scheduler_status() -> dict:
    """
    Get the current status of the conversation analyzer scheduler.
    
    Returns:
        dict: Status information including running state and configuration
    """
    manager = get_service_manager()
    return await manager.get_status()

async def trigger_manual_analysis_check() -> dict:
    """
    Manually trigger a check for sessions needing analysis.
    
    Useful for testing or debugging the automatic analysis system.
    
    Returns:
        dict: Results of the manual check including analysis outcomes
    """
    manager = get_service_manager()
    return await manager.run_manual_check()

async def cleanup_expired_sessions() -> int:
    """
    Clean up expired session entries from Redis.
    
    This is a maintenance function that can be called periodically
    to remove stale session data.
    
    Returns:
        int: Number of expired sessions cleaned up
    """
    manager = get_service_manager()
    return await manager.cleanup_expired_sessions()

# Context manager for easy integration
class ConversationSchedulerContext:
    """
    Async context manager for the conversation scheduler service.
    
    Usage:
        async with ConversationSchedulerContext():
            # Your main application code here
            # Scheduler will start automatically and stop on exit
            pass
    """
    
    def __init__(self):
        self.manager = get_service_manager()
    
    async def __aenter__(self):
        success = await self.manager.start()
        if not success:
            raise RuntimeError("Failed to start conversation scheduler service")
        return self.manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.manager.stop()

# Example usage functions for testing
async def example_startup_integration():
    """
    Example of how to integrate the scheduler service with your application startup.
    
    This shows the recommended pattern for starting the service when your
    application starts up.
    """
    logger.info("🚀 Application starting up...")
    
    # Start the conversation analyzer scheduler
    scheduler_started = await start_conversation_scheduler()
    
    if scheduler_started:
        logger.info("✅ All services started successfully")
        
        # Get and log status
        status = await get_scheduler_status()
        logger.info(f"📊 Scheduler Status: {status}")
        
    else:
        logger.error("❌ Failed to start scheduler service")
        # You might want to exit or continue without the scheduler
        # depending on your application requirements
    
    return scheduler_started

async def example_shutdown_integration():
    """
    Example of how to integrate the scheduler service with your application shutdown.
    
    This shows the recommended pattern for stopping the service when your
    application shuts down.
    """
    logger.info("🛑 Application shutting down...")
    
    # Stop the conversation analyzer scheduler
    scheduler_stopped = await stop_conversation_scheduler()
    
    if scheduler_stopped:
        logger.info("✅ All services stopped successfully")
    else:
        logger.error("❌ Error during service shutdown")
    
    logger.info("👋 Application shutdown complete")
    
    return scheduler_stopped

# For testing the system
async def test_scheduler_system():
    """
    Test function to verify the scheduler system is working correctly.
    
    This function can be used to test the entire automatic conversation
    analysis system end-to-end.
    """
    logger.info("🧪 Testing Conversation Scheduler System...")
    
    try:
        # Start the scheduler
        started = await start_conversation_scheduler()
        if not started:
            logger.error("Failed to start scheduler for testing")
            return False
        
        # Get status
        status = await get_scheduler_status()
        logger.info(f"Scheduler Status: {status}")
        
        # Run manual check
        check_results = await trigger_manual_analysis_check()
        logger.info(f"Manual Check Results: {check_results}")
        
        # Cleanup expired sessions
        cleaned_count = await cleanup_expired_sessions()
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        # Stop the scheduler
        stopped = await stop_conversation_scheduler()
        if not stopped:
            logger.error("Failed to stop scheduler after testing")
            return False
        
        logger.info("✅ Scheduler system test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Scheduler system test failed: {str(e)}")
        return False
