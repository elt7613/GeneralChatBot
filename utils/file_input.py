import base64
import mimetypes
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic_ai import BinaryContent, DocumentUrl, ImageUrl


def _guess_media_type(path: Union[str, Path], default: str = "application/octet-stream") -> str:
    """Guess the media type from a file path or URL."""
    mime, _ = mimetypes.guess_type(str(path))
    return mime or default


def _bytes_from_maybe_base64(data: Union[str, bytes, bytearray]) -> bytes:
    """Decode base64 if a string is provided, otherwise return raw bytes."""
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        # Try base64 decode; if it fails, treat as raw text bytes
        try:
            return base64.b64decode(data, validate=False)
        except Exception:
            return data.encode()


async def file_to_prompt_parts(text: str, file_info: Optional[Union[Dict[str, Any], str, Path]]) -> List[Any]:
    """
    Build a list of prompt parts for PydanticAI from text + optional file info.

    Supported file_info shapes:
    - {"url": str}
    - {"path": str, "media_type"?: str}
    - {"bytes": (bytes|bytearray|base64_str), "media_type": str}
    - str or Path: treated as local path if not an http(s) URL, otherwise URL

    If the URL/path appears to be an image (image/*), ImageUrl is used.
    Otherwise, DocumentUrl for URLs, and BinaryContent for local bytes.
    """
    parts: List[Any] = [text]
    if not file_info:
        return parts

    # Accept plain string or Path objects for convenience
    if isinstance(file_info, (str, Path)):
        # URL or local path?
        s = str(file_info)
        if s.lower().startswith("http://") or s.lower().startswith("https://"):
            media_type = _guess_media_type(s)
            if media_type.startswith("image/"):
                parts.append(ImageUrl(url=s))
            else:
                parts.append(DocumentUrl(url=s))
            return parts
        # Local path
        p = Path(s)
        if p.exists() and p.is_file():
            data = await asyncio.to_thread(p.read_bytes)
            media_type = _guess_media_type(p)
            parts.append(BinaryContent(data=data, media_type=media_type))
        return parts

    # URL case
    url = file_info.get("url")  # type: ignore[assignment]
    if isinstance(url, str) and url:
        media_type = file_info.get("media_type") or _guess_media_type(url)
        if media_type.startswith("image/"):
            parts.append(ImageUrl(url=url))
        else:
            parts.append(DocumentUrl(url=url))
        return parts

    # Local path case
    path = file_info.get("path")  # type: ignore[assignment]
    if isinstance(path, str) and path:
        p = Path(path)
        if p.exists() and p.is_file():
            data = await asyncio.to_thread(p.read_bytes)
            media_type = file_info.get("media_type") or _guess_media_type(p)
            parts.append(BinaryContent(data=data, media_type=media_type))
            return parts
        else:
            # If path is invalid, just fall back to text-only
            return parts

    # Raw bytes case
    if "bytes" in file_info:
        media_type = file_info.get("media_type") or "application/octet-stream"
        data = _bytes_from_maybe_base64(file_info["bytes"])  # type: ignore[index]
        parts.append(BinaryContent(data=data, media_type=media_type))
        return parts

    # Unknown structure -> ignore
    return parts
