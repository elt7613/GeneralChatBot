from langgraph.graph import StateGraph, START, END
from states.system_state import SystemState
from agents.companion.companion import companion_agent
from agents.companion.conversation_analyzer import conversation_analyzer_agent

async def router(state: SystemState):
    agent_name = state.get("agent_name")

    if agent_name is None:
        return "companion_agent"
    elif agent_name == "companion_agent":
        return "companion_agent"
    elif agent_name == "conversation_analyzer_agent":
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

companion_graph = graph.compile()