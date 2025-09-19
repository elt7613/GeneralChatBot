from typing_extensions import TypedDict, Optional, Literal, List, Dict, Any
from dataclasses import dataclass

from .user import UnserInput

@dataclass(kw_only=True)
class SystemState(TypedDict):
    user_id: str
    workflow_id: str

    agent_name: Literal["general_agent", "companion_agent", "conversation_analyzer_agent"]

    previous_agent: Optional[str]

    user_input: Optional[UnserInput]
    agent_response: Optional[str]
    
    