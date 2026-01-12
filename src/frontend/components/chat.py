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
    """
    for message in SessionState.get_messages():
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def render_chat_input() -> Optional[str]:
    """
    Render the chat input field and handle user input.

    Returns:
        The user's input message if provided, None otherwise
    """
    return st.chat_input(CHAT_INPUT_PLACEHOLDER)


def process_user_message(prompt: str, api_client: APIClient) -> None:
    """
    Process a user message and get response from the API.

    Args:
        prompt: The user's message
        api_client: APIClient instance for backend communication
    """
    # Add user message to history
    SessionState.add_message("user", prompt)

    # Display assistant response area
    with st.chat_message("assistant"):
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
                    st.markdown(assistant_message)
                    SessionState.add_message("assistant", assistant_message)
                else:
                    error_msg = "No response received from assistant"
                    st.error(error_msg)
                    SessionState.add_message("assistant", error_msg)
            else:
                # Show error message
                st.error(response.error)
                SessionState.add_message("assistant", response.error or "Unknown error")

    # Update last processed index
    SessionState.set_last_processed_idx(SessionState.get_message_count() - 1)

    # Rerun to update UI
    st.rerun()


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
            process_user_message(last_msg["content"], api_client)
            return

    # Handle new user input
    user_input = render_chat_input()
    if user_input:
        process_user_message(user_input, api_client)
