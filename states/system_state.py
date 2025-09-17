from typing_extensions import TypedDict, Optional, Literal, List, Dict, Any
from dataclasses import dataclass

@dataclass(kw_only=True)
class SystemState(TypedDict):
    user_id: str
    workflow_id: str

    next: Literal["general_agent", "summarize_conversation"] = None

    user_input: Optional[str]
    agent_response: Optional[str]
    
    