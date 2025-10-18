from typing_extensions import TypedDict, Optional, Literal, List, Dict, Any
from dataclasses import dataclass

from .user import UnserInput

@dataclass(kw_only=True)
class SystemState(TypedDict):
    user_id: str
    workflow_id: str

    system: Literal["journal", "companion"] = None
    agent_name: Literal["companion_agent", "conversation_analyzer_agent"] = None

    previous_agent: Optional[str]

    user_input: Optional[UnserInput]
    agent_response: Optional[str]
    conversation_analyzed: Optional[str]
    journal_analysis: Optional[Dict[str, Any]]