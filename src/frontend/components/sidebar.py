"""
Sidebar component for MTL Finder.
"""

import streamlit as st

from config import DESTINATIONS, ABOUT_TEXT, GITHUB_URL
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
        # The empty string allows for a placeholder option, without pre-selecting any destination
        # This way we just check if selected_dest is different than "" to know if user made a selection
        [""] + DESTINATIONS,
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

    # GitHub link
    st.link_button("🔗 View on GitHub", GITHUB_URL, use_container_width=True)


def render_action_buttons() -> None:
    """
    Render action button for creating new session.
    """
    if st.button("🔄 New Session", use_container_width=True):
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
        # Popular destinations
        render_popular_destinations()
        st.divider()

        # Location status
        display_location_status()
        st.divider()

        # About section
        render_about_section()
