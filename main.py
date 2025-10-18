from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from states.system_state import SystemState
from graphs.companion import companion_graph
from graphs.journal import journal_graph

import os
from dotenv import load_dotenv

load_dotenv()

async def router(state: SystemState):
    if state.get("system") == "journal":
        return "journal_graph"
    elif state.get("system") == "companion":
        return "companion_graph"
    else:
        return END
        
graph = StateGraph(SystemState)

graph.add_node("companion_graph", companion_graph)
graph.add_node("journal_graph", journal_graph)

graph.add_conditional_edges(    
    START,
    router,
    {
        "companion_graph": "companion_graph",
        "journal_graph": "journal_graph",
        END: END
    }
)

graph.add_edge("companion_graph", END)
graph.add_edge("journal_graph", END)

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