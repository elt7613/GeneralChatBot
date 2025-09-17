from langgraph.graph import StateGraph, START, END
from states.system_state import SystemState
from agent.conversation_summarizer import summarization_agent
from pydantic_ai.usage import UsageLimits
from agent.history import GeneralAgentHistory
import os
import asyncio
from dotenv import load_dotenv

async def summarize_conversation(state: SystemState):
    """
    Summarize a conversation using the summarization agent.
    
    Args:
        conversation_messages: List of message dictionaries with 'user' and 'assistant' keys
        workflow_id: The workflow ID of the conversation
        user_id: Optional user ID for context
        
    Returns:
        ConversationSummary: Structured summary of the conversation
    """
    # Conversation history
    history = await GeneralAgentHistory.load_or_create(state.get("workflow_id"))
    
    prompt = f"""
    Conversation History:
    {history.messages}

    Summarize the conversation intents.
    """

    try:
        # Use async version of the agent
        result = await summarization_agent.run(
            prompt,
            usage_limits=UsageLimits(request_limit=None)
        )

        # Ensure directory exists (async)
        await asyncio.to_thread(os.makedirs, "conversation_summary", exist_ok=True)

        data = f"""
        # Main Intent: 
        {result.output.main_intent}
        
        # Key Points: 
        {result.output.key_points}
        
        # Summary: 
        {result.output.summary}
        
        # Message Count: 
        {result.output.message_count}
        
        # Conversation Topics: 
        {result.output.conversation_topics}
        """
        
        # Write file asynchronously
        def write_file():
            with open(f"conversation_summary/{state.get('workflow_id')}.md", "w") as f:
                f.write(data)
        
        await asyncio.to_thread(write_file)
    except Exception as e:
        raise Exception(f"Agent failed: {e}")

    return {
        "next": END
    }

summarize_conversation_graph = StateGraph(SystemState)

summarize_conversation_graph.add_node("summarize_conversation",summarize_conversation)

summarize_conversation_graph.add_edge(START, "summarize_conversation")
summarize_conversation_graph.add_edge("summarize_conversation", END)

# Compile the graph
compiled_summarize_conversation_graph = summarize_conversation_graph.compile()
