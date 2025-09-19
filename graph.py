from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from states.system_state import SystemState
from agent.companion import companion_agent
from agent.conversation_analyzer import conversation_analyzer_agent
from agent.general import general_agent


import os
from dotenv import load_dotenv

load_dotenv()

async def router(state: SystemState):
    if state.get("agent_name") == "general_agent":
        return "general_agent"
    elif state.get("agent_name") == "companion_agent":
        return "companion_agent"
    elif state.get("agent_name") == "conversation_analyzer_agent":
        return "conversation_analyzer_agent"
    else:
        return END
        
graph = StateGraph(SystemState)

graph.add_node("general_agent", general_agent)
graph.add_node("companion_agent", companion_agent)
graph.add_node("conversation_analyzer_agent", conversation_analyzer_agent)

graph.add_conditional_edges(
    START,
    router,
    {
        "general_agent": "general_agent",
        "companion_agent": "companion_agent",
        "conversation_analyzer_agent": "conversation_analyzer_agent",
        END: END
    }
)

graph.add_edge("general_agent", END)
graph.add_edge("companion_agent", END)
graph.add_edge("conversation_analyzer_agent", END)

DB_URI = os.environ.get("MONGO_CONNECTION_URL")

#Compile and return the workflow graph
with MongoDBSaver.from_conn_string(DB_URI) as checkpointer:
    graph.compile(checkpointer=checkpointer)