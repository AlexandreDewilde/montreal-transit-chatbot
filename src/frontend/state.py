"""
Session state management for MTL Finder.
"""
import streamlit as st
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class UserLocation:
    """User's geographic location."""
    latitude: float
    longitude: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format for API."""
        return {"latitude": self.latitude, "longitude": self.longitude}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "UserLocation":
        """Create from dictionary."""
        return cls(latitude=data["latitude"], longitude=data["longitude"])


@dataclass
class ChatMessage:
    """A chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ChatMessage":
        """Create from dictionary."""
        return cls(role=data["role"], content=data["content"])


class SessionState:
    """
    Manages the application session state.

    Provides a clean interface to Streamlit's session_state.
    """

    # Session state keys
    SESSION_ID_KEY = "session_id"
    MESSAGES_KEY = "messages"
    USER_LOCATION_KEY = "user_location"
    LOCATION_REQUESTED_KEY = "location_requested"
    LAST_PROCESSED_IDX_KEY = "last_processed_idx"

    @classmethod
    def initialize(cls) -> None:
        """Initialize session state with default values."""
        if cls.SESSION_ID_KEY not in st.session_state:
            st.session_state[cls.SESSION_ID_KEY] = None

        if cls.MESSAGES_KEY not in st.session_state:
            st.session_state[cls.MESSAGES_KEY] = []

        if cls.USER_LOCATION_KEY not in st.session_state:
            st.session_state[cls.USER_LOCATION_KEY] = None

        if cls.LOCATION_REQUESTED_KEY not in st.session_state:
            st.session_state[cls.LOCATION_REQUESTED_KEY] = False

        if cls.LAST_PROCESSED_IDX_KEY not in st.session_state:
            st.session_state[cls.LAST_PROCESSED_IDX_KEY] = -1

    # Session ID
    @classmethod
    def get_session_id(cls) -> Optional[str]:
        """Get the current session ID."""
        return st.session_state.get(cls.SESSION_ID_KEY)

    @classmethod
    def set_session_id(cls, session_id: str) -> None:
        """Set the session ID."""
        st.session_state[cls.SESSION_ID_KEY] = session_id

    # Messages
    @classmethod
    def get_messages(cls) -> List[Dict[str, str]]:
        """Get all chat messages."""
        return st.session_state.get(cls.MESSAGES_KEY, [])

    @classmethod
    def add_message(cls, role: str, content: str) -> None:
        """Add a message to the chat history."""
        message = {"role": role, "content": content}
        st.session_state[cls.MESSAGES_KEY].append(message)

    @classmethod
    def clear_messages(cls) -> None:
        """Clear all chat messages."""
        st.session_state[cls.MESSAGES_KEY] = []

    @classmethod
    def get_message_count(cls) -> int:
        """Get the number of messages."""
        return len(st.session_state.get(cls.MESSAGES_KEY, []))

    @classmethod
    def get_last_message(cls) -> Optional[Dict[str, str]]:
        """Get the last message in the chat."""
        messages = cls.get_messages()
        return messages[-1] if messages else None

    # User Location
    @classmethod
    def get_user_location(cls) -> Optional[UserLocation]:
        """Get the user's location."""
        loc_dict = st.session_state.get(cls.USER_LOCATION_KEY)
        if loc_dict:
            return UserLocation.from_dict(loc_dict)
        return None

    @classmethod
    def set_user_location(cls, latitude: float, longitude: float) -> None:
        """Set the user's location."""
        location = UserLocation(latitude=latitude, longitude=longitude)
        st.session_state[cls.USER_LOCATION_KEY] = location.to_dict()

    @classmethod
    def has_location(cls) -> bool:
        """Check if user location is available."""
        return st.session_state.get(cls.USER_LOCATION_KEY) is not None

    # Location Requested
    @classmethod
    def is_location_requested(cls) -> bool:
        """Check if location was requested."""
        return st.session_state.get(cls.LOCATION_REQUESTED_KEY, False)

    @classmethod
    def set_location_requested(cls, requested: bool) -> None:
        """Set location requested flag."""
        st.session_state[cls.LOCATION_REQUESTED_KEY] = requested

    # Last Processed Index
    @classmethod
    def get_last_processed_idx(cls) -> int:
        """Get the last processed message index."""
        return st.session_state.get(cls.LAST_PROCESSED_IDX_KEY, -1)

    @classmethod
    def set_last_processed_idx(cls, idx: int) -> None:
        """Set the last processed message index."""
        st.session_state[cls.LAST_PROCESSED_IDX_KEY] = idx

    # Utility Methods
    @classmethod
    def reset_session(cls) -> None:
        """Reset the entire session state."""
        st.session_state[cls.SESSION_ID_KEY] = None
        st.session_state[cls.MESSAGES_KEY] = []
        st.session_state[cls.LAST_PROCESSED_IDX_KEY] = -1

    @classmethod
    def should_process_message(cls) -> bool:
        """
        Check if there's a new user message that needs processing.

        Returns:
            True if last message is from user and hasn't been processed yet.
        """
        last_msg = cls.get_last_message()
        if not last_msg or last_msg["role"] != "user":
            return False

        current_idx = cls.get_message_count() - 1
        return current_idx > cls.get_last_processed_idx()
