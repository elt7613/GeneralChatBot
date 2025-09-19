from typing_extensions import TypedDict, Optional, Literal, List, Dict, Any
from dataclasses import dataclass


@dataclass(kw_only=True)
class UnserInput(TypedDict):
    response: Optional[str]
    companion_name: Optional[str] = ""
    companion_gender: Optional[str] = ""
    file: Optional[object] = None