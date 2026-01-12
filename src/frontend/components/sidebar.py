"""
Sidebar component for MTL Finder.
"""
import streamlit as st

from config import DESTINATIONS, ABOUT_TEXT
from state import SessionState
from components.location import display_location_status


def render_popular_destinations() -> None:
    """
    Render the popular destinations selector.

    Allows users to quickly select a destination and get directions.
    """
    st.header("🎯 Popular Destinations")

    selected_dest = st.selectbox(
        "Quick destination select:",
        [""] + list(DESTINATIONS.keys()),
        format_func=lambda x: "Choose a destination..." if x == "" else x,
    )

    if selected_dest:
        if st.button(f"🗺️ Get directions to {selected_dest}"):
            prompt = f"How do I get to {selected_dest}?"
            SessionState.add_message("user", prompt)
            st.rerun()


def render_about_section() -> None:
    """
    Render the about section with app information.
    """
    st.header("ℹ️ About")
    st.caption(ABOUT_TEXT)


def render_action_buttons() -> None:
    """
    Render action buttons for clearing chat and creating new session.
    """
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Chat"):
            SessionState.clear_messages()
            st.rerun()

    with col2:
        if st.button("🔄 New Session"):
            SessionState.reset_session()
            st.rerun()


def render_sidebar() -> None:
    """
    Render the complete sidebar with all sections.

    Includes:
    - Location status
    - Popular destinations
    - About section
    - Action buttons
    """
    with st.sidebar:
        # Location status
        display_location_status()
        st.divider()

        # Popular destinations
        render_popular_destinations()
        st.divider()

        # About section
        render_about_section()
        st.divider()

        # Action buttons
        render_action_buttons()
