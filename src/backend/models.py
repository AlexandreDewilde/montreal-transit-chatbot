"""
Pydantic models for MTL Finder backend API
"""

from typing import List, Optional
from pydantic import BaseModel


class UserLocation(BaseModel):
    """User's geographic location from browser/device GPS"""

    latitude: float
    longitude: float


class Message(BaseModel):
    """Incoming chat message from user"""

    content: str
    session_id: str
    user_location: Optional[UserLocation] = None


class ChatMessage(BaseModel):
    """Single message in a conversation (user or assistant)"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ChatResponse(BaseModel):
    """Response containing all messages in a session"""

    session_id: str
    messages: List[ChatMessage]
