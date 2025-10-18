import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from states.system_state import SystemState

logger = logging.getLogger(__name__)

class TriggerService:
    """
    Service responsible for triggering LangGraph workflows for conversation analysis.
    
    This service handles the invocation of the conversation_analyzer_agent through
    the LangGraph workflow system when sessions are approaching expiry.
    """
    
    def __init__(self, graph_factory: Optional[Callable] = None):
        """
        Initialize the trigger service.
        
        Args:
            graph_factory: Optional factory function that returns a compiled LangGraph instance
        """
        self.graph = None
        self.graph_factory = graph_factory
        if graph_factory:
            self._initialize_graph()
    
    def _initialize_graph(self):
        """Initialize the LangGraph instance using the factory function."""
        if not self.graph_factory:
            logger.warning("TriggerService: No graph factory provided, cannot initialize LangGraph")
            return
            
        try:
            self.graph = self.graph_factory()
            logger.info(f"TriggerService: LangGraph initialized successfully - Type: {type(self.graph)}")
            
            # Verify the graph has the required methods
            if not hasattr(self.graph, 'ainvoke'):
                logger.error("TriggerService: Graph object missing ainvoke method")
                self.graph = None
                
        except Exception as e:
            logger.error(f"TriggerService: Failed to initialize LangGraph: {str(e)}")
            self.graph = None
    
    async def trigger_conversation_analysis(
        self, 
        user_id: str, 
        workflow_id: str, 
        agent_name: str
    ) -> bool:
        """
        Trigger the conversation analyzer agent for a specific session.
        
        Args:
            user_id: The unique identifier for the user
            workflow_id: The unique identifier for the workflow/conversation
            agent_name: The name of the original agent (general_agent, companion_agent)
            
        Returns:
            bool: True if analysis was triggered successfully, False otherwise
        """
        if not self.graph:
            logger.error("TriggerService: LangGraph not initialized, cannot trigger analysis")
            return False
            
        if not all([user_id, workflow_id, agent_name]):
            logger.error("TriggerService: Invalid arguments - all parameters must be provided")
            return False
            
        try:
            # Create SystemState for conversation analyzer
            state = SystemState(
                user_id=user_id,
                workflow_id=workflow_id,
                agent_name="conversation_analyzer_agent",
                previous_agent=agent_name,
                user_input=None,
                agent_response=None
            )
            
            # Configuration for LangGraph execution
            config = {
                "configurable": {
                    "thread_id": workflow_id
                }
            }
            
            logger.info(f"Triggering conversation analysis for workflow: {workflow_id}, user: {user_id}, previous_agent: {agent_name}")
            
            # Invoke the LangGraph workflow directly
            result = await self.graph.ainvoke(state, config)
            
            if result:
                logger.info(f"Successfully completed conversation analysis for workflow: {workflow_id}")
                return True
            else:
                logger.warning(f"Conversation analysis returned empty result for workflow: {workflow_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to trigger conversation analysis for workflow {workflow_id}: {str(e)}")
            return False
    
    async def trigger_multiple_analyses(self, sessions: list) -> Dict[str, bool]:
        """
        Trigger conversation analysis for multiple sessions concurrently.
        
        Args:
            sessions: List of session dictionaries containing user_id, workflow_id, agent_name
            
        Returns:
            Dict[str, bool]: Dictionary mapping workflow_id to success status
        """
        if not sessions:
            logger.debug("TriggerService: No sessions to analyze")
            return {}
            
        logger.info(f"Triggering analysis for {len(sessions)} sessions")
        
        # Create tasks for concurrent execution
        tasks = []
        workflow_ids = []
        
        for session in sessions:
            user_id = session.get('user_id')
            workflow_id = session.get('workflow_id')
            agent_name = session.get('agent_name')
            
            if not all([user_id, workflow_id, agent_name]):
                logger.warning(f"Skipping invalid session: {session}")
                continue
                
            # Skip if already analyzed
            if session.get('analyzed', False):
                logger.debug(f"Skipping already analyzed session: {workflow_id}")
                continue
                
            task = self.trigger_conversation_analysis(user_id, workflow_id, agent_name)
            tasks.append(task)
            workflow_ids.append(workflow_id)
        
        if not tasks:
            logger.info("No valid sessions to analyze")
            return {}
        
        # Execute all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            analysis_results = {}
            for i, result in enumerate(results):
                workflow_id = workflow_ids[i]
                if isinstance(result, Exception):
                    logger.error(f"Analysis failed for workflow {workflow_id}: {str(result)}")
                    analysis_results[workflow_id] = False
                else:
                    analysis_results[workflow_id] = bool(result)
            
            successful_count = sum(1 for success in analysis_results.values() if success)
            logger.info(f"Completed analysis for {successful_count}/{len(analysis_results)} sessions")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error during batch analysis: {str(e)}")
            return {wid: False for wid in workflow_ids}
    
    def is_healthy(self) -> bool:
        """
        Check if the trigger service is healthy and ready to process requests.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        return self.graph is not None
    
    def set_graph_factory(self, graph_factory: Callable):
        """
        Set the graph factory function and initialize the graph.
        
        Args:
            graph_factory: Factory function that returns a compiled LangGraph instance
        """
        self.graph_factory = graph_factory
        self._initialize_graph()
    
    async def reinitialize(self) -> bool:
        """
        Reinitialize the LangGraph instance in case of failure.
        
        Returns:
            bool: True if reinitialization was successful, False otherwise
        """
        try:
            logger.info("Reinitializing TriggerService...")
            self._initialize_graph()
            return self.is_healthy()
        except Exception as e:
            logger.error(f"Failed to reinitialize TriggerService: {str(e)}")
            return False
