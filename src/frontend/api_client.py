"""
API client for communicating with MTL Finder backend.
"""
import requests
import time
import uuid
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from config import (
    API_URL,
    API_TIMEOUT,
    API_RETRY_ATTEMPTS,
    API_RETRY_DELAY,
    ERROR_API_CONNECTION,
    ERROR_API_STATUS,
)


@dataclass
class ChatResponse:
    """Response from the chat API."""
    success: bool
    messages: List[Dict[str, str]]
    error: Optional[str] = None

    def get_last_assistant_message(self) -> Optional[str]:
        """Extract the last assistant message from the response."""
        if not self.success or not self.messages:
            return None

        assistant_messages = [
            msg["content"] for msg in self.messages if msg["role"] == "assistant"
        ]
        return assistant_messages[-1] if assistant_messages else None


class APIClient:
    """
    Client for communicating with the MTL Finder backend API.

    Handles session management, chat requests, and implements retry logic.
    """

    def __init__(
        self,
        base_url: str = API_URL,
        timeout: int = API_TIMEOUT,
        retry_attempts: int = API_RETRY_ATTEMPTS,
        retry_delay: int = API_RETRY_DELAY,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the backend API
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        retry: bool = True,
    ) -> requests.Response:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            json_data: JSON payload for the request
            retry: Whether to retry on failure

        Returns:
            Response object

        Raises:
            requests.exceptions.RequestException: If all retries fail
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        attempts = self.retry_attempts if retry else 1

        last_exception: Optional[requests.exceptions.RequestException] = None
        for attempt in range(attempts):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=json_data,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                break

        # All retries failed
        if last_exception:
            raise last_exception
        raise requests.exceptions.RequestException("Request failed with no exception")

    def create_session(self) -> Optional[str]:
        """
        Create a new session on the backend.

        Returns:
            Session ID if successful, None otherwise
        """
        try:
            response = self._make_request("POST", "/session", retry=False)
            if response.status_code == 200:
                data = response.json()
                return data.get("session_id")
        except requests.exceptions.RequestException:
            pass

        # Fallback to local UUID
        return str(uuid.uuid4())

    def send_chat_message(
        self,
        content: str,
        session_id: str,
        user_location: Optional[Dict[str, float]] = None,
    ) -> ChatResponse:
        """
        Send a chat message to the backend.

        Args:
            content: User's message content
            session_id: Current session ID
            user_location: Optional user location dict with latitude/longitude

        Returns:
            ChatResponse with success status and messages or error
        """
        try:
            # Prepare payload
            payload = {
                "content": content,
                "session_id": session_id,
            }

            # Add user location if provided
            if user_location:
                payload["user_location"] = user_location

            # Send request
            response = self._make_request("POST", "/chat", json_data=payload)

            if response.status_code == 200:
                data = response.json()
                return ChatResponse(
                    success=True,
                    messages=data.get("messages", []),
                )
            else:
                error_msg = ERROR_API_STATUS.format(status=response.status_code)
                return ChatResponse(
                    success=False,
                    messages=[],
                    error=error_msg,
                )

        except requests.exceptions.RequestException as e:
            error_msg = ERROR_API_CONNECTION.format(error=str(e))
            return ChatResponse(
                success=False,
                messages=[],
                error=error_msg,
            )

    def health_check(self) -> bool:
        """
        Check if the backend API is healthy.

        Returns:
            True if API is reachable and healthy, False otherwise
        """
        try:
            response = self._make_request("GET", "/health", retry=False)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
