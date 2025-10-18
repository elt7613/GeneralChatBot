from typing_extensions import TypedDict, Optional, Literal, List, Dict, Any
from dataclasses import dataclass


@dataclass(kw_only=True)
class UnserInput(TypedDict):
    response: Optional[str]
    companion_name: Optional[str] = ""
    companion_gender: Optional[str] = ""
    # File can be provided in one of the following shapes:
    # - {"url": str, "media_type"?: str}
    # - {"path": str, "media_type"?: str}
    # - {"bytes": (bytes|bytearray|base64_str), "media_type": str}
    file: Optional[Dict[str, Any]] = None