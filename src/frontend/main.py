"""
MTL Finder - Your intelligent travel assistant for Montreal.

Powered by Mistral AI & OpenTripPlanner with real-time STM data.
"""
import streamlit as st

from config import PAGE_TITLE, PAGE_ICON, LAYOUT, APP_TITLE, APP_CAPTION
from state import SessionState
from api_client import APIClient
from components import (
    render_location_handler,
    render_quick_actions,
    render_chat_interface,
    render_sidebar,
)


def initialize_app() -> None:
    """
    Initialize the application.

    Sets up page configuration and session state.
    """
    # Configure page
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
    )

    # Initialize session state
    SessionState.initialize()


def initialize_session(api_client: APIClient) -> None:
    """
    Initialize or retrieve the backend session.

    Args:
        api_client: APIClient instance
    """
    if SessionState.get_session_id() is None:
        session_id = api_client.create_session()
        SessionState.set_session_id(session_id or "")


def render_header() -> None:
    """Render the app title and description."""
    st.title(APP_TITLE)
    st.caption(APP_CAPTION)


def main() -> None:
    """
    Main application entry point.

    Orchestrates the entire application flow.
    """
    # Initialize app
    initialize_app()

    # Create API client
    api_client = APIClient()

    # Initialize session
    initialize_session(api_client)

    # Render header
    render_header()

    # Handle location acquisition
    render_location_handler()

    # Render quick action buttons (if no messages)
    render_quick_actions()

    # Render chat interface
    render_chat_interface(api_client)

    # Render sidebar
    render_sidebar()


if __name__ == "__main__":
    main()
