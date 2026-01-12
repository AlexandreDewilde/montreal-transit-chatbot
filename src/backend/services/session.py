"""
Session storage and management for chat conversations
"""

from typing import Dict, List


class SessionStore:
    """In-memory session storage for chat conversations"""

    def __init__(self):
        """Initialize in-memory storage"""
        self._sessions: Dict[str, List[dict]] = {}

    def create_session(self, session_id: str) -> None:
        """
        Create a new session

        Args:
            session_id: Unique session identifier
        """
        self._sessions[session_id] = []

    def get_messages(self, session_id: str) -> List[dict]:
        """
        Get all messages for a session

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]

    def add_message(self, session_id: str, message: dict) -> None:
        """
        Add a message to a session

        Args:
            session_id: Session identifier
            message: Message dictionary with role, content, timestamp
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(message)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists

        Args:
            session_id: Session identifier

        Returns:
            True if session exists, False otherwise
        """
        return session_id in self._sessions
