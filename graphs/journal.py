from langgraph.graph import StateGraph, START, END
from states.system_state import SystemState
from agents.journal.journal_analyzer import journal_analyzer_agent


graph = StateGraph(SystemState)

graph.add_node("journal_analyzer_agent", journal_analyzer_agent)

graph.add_edge(START, "journal_analyzer_agent")
graph.add_edge("journal_analyzer_agent", END)

journal_graph = graph.compile()