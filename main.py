from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from states.system_state import SystemState
from agent.general_agent import general_agent as pydantic_agent
from pydantic_ai.usage import UsageLimits
from agent.history import GeneralAgentHistory
from graphs.conversation_summary import compiled_summarize_conversation_graph
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def general_agent_node(state: SystemState):
    # Conversation history
    history = await GeneralAgentHistory.load_or_create(state.get("workflow_id"))
    
    user_input = state.get("user_input", '')
    
    composed_input = f"Conversation so far:\n{history.messages}\n\nUser: {user_input}"

    try:
        # Use async version of the agent
        result = await pydantic_agent.run(
            composed_input,
            usage_limits=UsageLimits(request_limit=None)
        )
    except Exception as e:
        raise Exception(f"Agent failed: {e}")

    history.messages.append({
        "user": user_input,
        "assistant": result.output.response
    })
    await history.save(state.get("workflow_id"))

    return {
        "agent_response": result.output.response,
        "next": "user_input"
    }

async def summarize_conversation_node(state: SystemState):
    result = await compiled_summarize_conversation_graph.ainvoke(state)
    return result

async def router(state: SystemState):
    if state.get("next") == "general_agent":
        return "general_agent"
    elif state.get("next") == "summarize_conversation":
        return "summarize_conversation"
    else:
        return END
        
graph = StateGraph(SystemState)

graph.add_node("general_agent", general_agent_node)
graph.add_node("summarize_conversation", summarize_conversation_node)

graph.add_conditional_edges(
    START,
    router,
    {
        "general_agent": "general_agent",
        "summarize_conversation": "summarize_conversation",
        END: END
    }
)

graph.add_conditional_edges(
    "general_agent",
    router,
    {
        "general_agent": "general_agent",
        "summarize_conversation": "summarize_conversation",
        END: END
    }
)

graph.add_conditional_edges(
    "summarize_conversation",
    router,
    {
        "general_agent": "general_agent", 
        "summarize_conversation": "summarize_conversation",
        END: END
    }
)

DB_URI = os.environ.get("MONGO_CONNECTION_URL")

#Compile and return the workflow graph
with MongoDBSaver.from_conn_string(DB_URI) as checkpointer:
    graph.compile(checkpointer=checkpointer)