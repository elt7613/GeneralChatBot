from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from states.system_state import SystemState
from agent.companion import companion_agent
from agent.conversation_analyzer import conversation_analyzer_agent

import os
from dotenv import load_dotenv

load_dotenv()

async def router(state: SystemState):
    if state.get("agent_name") == "companion_agent":
        return "companion_agent"
    elif state.get("agent_name") == "conversation_analyzer_agent":
        return "conversation_analyzer_agent"
    else:
        return END
        
graph = StateGraph(SystemState)

graph.add_node("companion_agent", companion_agent)
graph.add_node("conversation_analyzer_agent", conversation_analyzer_agent)

graph.add_conditional_edges(
    START,
    router,
    {
        "companion_agent": "companion_agent",
        "conversation_analyzer_agent": "conversation_analyzer_agent",
        END: END
    }
)

graph.add_edge("companion_agent", END)
graph.add_edge("conversation_analyzer_agent", END)

DB_URI = os.environ.get("MONGO_CONNECTION_URL")

# Compiling the workflow graph
def create_graph():
    checkpointer = MongoDBSaver.from_conn_string(DB_URI)
    return graph.compile(checkpointer=checkpointer)

# Scheduler-specific graph without checkpointer (for background processing)
def create_scheduler_graph():
    return graph.compile()

# Compiled graph for langgraph dev
compiled_graph = create_graph()