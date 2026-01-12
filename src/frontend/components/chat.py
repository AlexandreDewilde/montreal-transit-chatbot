"""
Chat interface component for MTL Finder.
"""

import streamlit as st
from typing import Optional

from config import CHAT_INPUT_PLACEHOLDER, THINKING_MESSAGE
from state import SessionState
from api_client import APIClient


def render_chat_messages() -> None:
    """
    Render all chat messages in the conversation.

    Displays messages in chat message containers with proper role (user/assistant).
    Supports different message types (error, warning, info, normal).
    """
    for message in SessionState.get_messages():
        with st.chat_message(message["role"]):
            message_type = message.get("message_type", "normal")

            if message_type == "error":
                st.error(message["content"])
            elif message_type == "warning":
                st.warning(message["content"])
            elif message_type == "info":
                st.info(message["content"])
            else:
                st.markdown(message["content"])


def render_chat_input() -> Optional[str]:
    """
    Render the chat input field and handle user input.

    Returns:
        The user's input message if provided, None otherwise
    """
    return st.chat_input(CHAT_INPUT_PLACEHOLDER)


def process_api_response(prompt: str, api_client: APIClient) -> None:
    """
    Get the API response for a user message and add it to chat history.

    Assumes the user message is already in the chat history.

    Args:
        prompt: The user's message content
        api_client: APIClient instance for backend communication
    """
    # Show spinner while processing
    with st.spinner(THINKING_MESSAGE):
        # Get user location if available
        user_location = None
        if SessionState.has_location():
            loc = SessionState.get_user_location()
            if loc:
                user_location = loc.to_dict()

        # Send message to API
        response = api_client.send_chat_message(
            content=prompt,
            session_id=SessionState.get_session_id() or "",
            user_location=user_location,
        )

        if response.success:
            # Get the assistant's response
            assistant_message = response.get_last_assistant_message()
            if assistant_message:
                SessionState.add_message("assistant", assistant_message)
            else:
                error_msg = "No response received from assistant"
                SessionState.add_message("assistant", error_msg, message_type="error")
        else:
            # Add error message
            SessionState.add_message(
                "assistant", response.error or "Unknown error", message_type="error"
            )

    # Update last processed index
    SessionState.set_last_processed_idx(SessionState.get_message_count() - 1)

    # Rerun to update UI
    st.rerun()


def process_user_message(prompt: str, api_client: APIClient) -> None:
    """
    Process a user message: add to history and get API response.

    Args:
        prompt: The user's message
        api_client: APIClient instance for backend communication
    """
    # Add user message to history
    SessionState.add_message("user", prompt)
    # Rerun to add the message to the chat display
    st.rerun()

    # Get and display API response
    process_api_response(prompt, api_client)


def render_chat_interface(api_client: APIClient) -> None:
    """
    Render the complete chat interface.

    Handles both message display and input processing.

    Args:
        api_client: APIClient instance for backend communication
    """
    # Render existing messages
    render_chat_messages()

    # Check if we need to process a message from quick actions
    if SessionState.should_process_message():
        last_msg = SessionState.get_last_message()
        if last_msg:
            # Process API response (message already added by quick_actions)
            process_api_response(last_msg["content"], api_client)
            return

    # Handle new user input
    user_input = render_chat_input()
    if user_input:
        # Add message and process response
        process_user_message(user_input, api_client)
