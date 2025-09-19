import logging
import asyncio
from typing import Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timezone

from ..config import SCHEDULER_INTERVAL_SECONDS, TRIGGER_OFFSET_MINUTES
from ..session_registry import SessionRegistry
from .trigger_service import TriggerService

logger = logging.getLogger(__name__)

class ConversationScheduler:
    """
    Background scheduler that automatically triggers conversation analysis for expiring sessions.
    
    This scheduler runs continuously in the background, checking for Redis sessions
    that are approaching expiry and triggering the conversation analyzer agent
    for each qualifying session.
    """
    
    def __init__(self, graph_factory: Optional[Callable] = None):
        """Initialize the conversation scheduler."""
        self.scheduler = None
        self.trigger_service = None
        self.is_running = False
        self._job_id = "conversation_analysis_job"
        
        # Initialize components
        self.trigger_service = TriggerService(graph_factory)
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler(
            timezone=timezone.utc,
            job_defaults={
                'coalesce': True,  # Combine multiple pending executions into one
                'max_instances': 1,  # Only one instance of the job can run at a time
                'misfire_grace_time': 30  # Grace period for missed executions
            }
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._on_job_executed, 
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._on_job_error, 
            EVENT_JOB_ERROR
        )
        
        logger.info("ConversationScheduler initialized")
    
    async def start(self):
        """Start the conversation scheduler."""
        if self.is_running:
            logger.warning("ConversationScheduler is already running")
            return False
            
        try:
            logger.info("Starting ConversationScheduler...")
            
            # Start the scheduler
            self.scheduler.start()
            
            # Add the job
            self.scheduler.add_job(
                self._check_expiring_sessions,
                trigger=IntervalTrigger(seconds=SCHEDULER_INTERVAL_SECONDS),
                id=self._job_id,
                name="Check Expiring Sessions",
                replace_existing=True
            )
            
            self.is_running = True
            logger.info(f"ConversationScheduler started successfully")
            logger.info(f"Job scheduled to run every {SCHEDULER_INTERVAL_SECONDS} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ConversationScheduler: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """
        Stop the background scheduler gracefully.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("ConversationScheduler is not running")
            return True
            
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("ConversationScheduler stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping ConversationScheduler: {str(e)}")
            return False
    
    async def _check_expiring_sessions(self):
        """
        Periodic job that checks for sessions expiring soon and triggers analysis.
        This method is called by the scheduler at regular intervals.
        """
        try:
            start_time = datetime.now(timezone.utc)
            logger.debug("Starting expiring sessions check")
            
            # Get sessions expiring within the offset minutes
            expiring_sessions = await SessionRegistry.get_sessions_expiring_soon(
                offset_minutes=TRIGGER_OFFSET_MINUTES
            )
            
            if not expiring_sessions:
                logger.debug("No sessions expiring soon")
                return
            
            logger.info(f"Found {len(expiring_sessions)} sessions expiring within {TRIGGER_OFFSET_MINUTES} minutes")
            
            # Filter out already analyzed sessions
            sessions_to_analyze = [
                session for session in expiring_sessions 
                if not session.get('analyzed', False)
            ]
            
            if not sessions_to_analyze:
                logger.info("All expiring sessions have already been analyzed")
                return
                
            logger.info(f"Triggering analysis for {len(sessions_to_analyze)} sessions")
            
            # Trigger analysis for all qualifying sessions
            analysis_results = await self.trigger_service.trigger_multiple_analyses(
                sessions_to_analyze
            )
            
            # Mark successful analyses as completed
            successful_analyses = []
            failed_analyses = []
            
            for workflow_id, success in analysis_results.items():
                if success:
                    successful_analyses.append(workflow_id)
                    # Mark session as analyzed
                    try:
                        await SessionRegistry.mark_session_analyzed(workflow_id)
                    except Exception as e:
                        logger.warning(f"Failed to mark session {workflow_id} as analyzed: {str(e)}")
                else:
                    failed_analyses.append(workflow_id)
            
            # Log results
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Expiring sessions check completed in {duration:.2f}s - "
                f"Successful: {len(successful_analyses)}, Failed: {len(failed_analyses)}"
            )
            
            if failed_analyses:
                logger.warning(f"Failed analyses for workflows: {failed_analyses}")
            
        except Exception as e:
            logger.error(f"Error during expiring sessions check: {str(e)}")
    
    def _on_job_executed(self, event):
        """Event handler for successful job execution."""
        logger.debug(f"Scheduled job '{event.job_id}' executed successfully")
    
    def _on_job_error(self, event):
        """Event handler for job execution errors."""
        logger.error(f"Scheduled job '{event.job_id}' failed: {str(event.exception)}")
    
    async def run_manual_check(self) -> dict:
        """
        Manually trigger a check for expiring sessions (for testing/debugging).
        
        Returns:
            dict: Results of the manual check including session count and analysis results
        """
        logger.info("Running manual expiring sessions check")
        
        try:
            start_time = datetime.now(timezone.utc)
            
            # Get expiring sessions
            expiring_sessions = await SessionRegistry.get_sessions_expiring_soon(
                offset_minutes=TRIGGER_OFFSET_MINUTES
            )
            
            sessions_to_analyze = [
                session for session in expiring_sessions 
                if not session.get('analyzed', False)
            ]
            
            # Trigger analyses
            analysis_results = {}
            if sessions_to_analyze:
                analysis_results = await self.trigger_service.trigger_multiple_analyses(
                    sessions_to_analyze
                )
                
                # Mark successful ones as analyzed
                for workflow_id, success in analysis_results.items():
                    if success:
                        await SessionRegistry.mark_session_analyzed(workflow_id)
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            return {
                'duration_seconds': duration,
                'total_expiring_sessions': len(expiring_sessions),
                'sessions_analyzed': len(sessions_to_analyze),
                'analysis_results': analysis_results,
                'successful_analyses': sum(1 for success in analysis_results.values() if success),
                'failed_analyses': sum(1 for success in analysis_results.values() if not success)
            }
            
        except Exception as e:
            logger.error(f"Error during manual check: {str(e)}")
            return {
                'error': str(e),
                'duration_seconds': 0,
                'total_expiring_sessions': 0,
                'sessions_analyzed': 0,
                'analysis_results': {},
                'successful_analyses': 0,
                'failed_analyses': 0
            }
    
    def get_status(self) -> dict:
        """
        Get the current status of the scheduler.
        
        Returns:
            dict: Status information including running state and configuration
        """
        return {
            'is_running': self.is_running,
            'scheduler_healthy': self.scheduler is not None,
            'trigger_service_healthy': self.trigger_service.is_healthy() if self.trigger_service else False,
            'interval_seconds': SCHEDULER_INTERVAL_SECONDS,
            'trigger_offset_minutes': TRIGGER_OFFSET_MINUTES,
            'next_run': self.scheduler.get_job(self._job_id).next_run_time.isoformat() if (
                self.is_running and self.scheduler.get_job(self._job_id)
            ) else None
        }
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired session entries (maintenance function).
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            return await SessionRegistry.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
            return 0

# Global scheduler instance
_scheduler_instance: Optional[ConversationScheduler] = None

async def get_scheduler(graph_factory: Optional[Callable] = None) -> ConversationScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ConversationScheduler(graph_factory)
    elif graph_factory and _scheduler_instance.trigger_service:
        # Update the graph factory if provided
        _scheduler_instance.trigger_service.set_graph_factory(graph_factory)
    return _scheduler_instance

async def start_scheduler(graph_factory: Optional[Callable] = None) -> bool:
    """Start the global conversation scheduler."""
    scheduler = await get_scheduler(graph_factory)
    return await scheduler.start()

async def stop_scheduler() -> bool:
    """Stop the global conversation scheduler."""
    global _scheduler_instance
    if _scheduler_instance:
        result = await _scheduler_instance.stop()
        _scheduler_instance = None
        return result
    return True
