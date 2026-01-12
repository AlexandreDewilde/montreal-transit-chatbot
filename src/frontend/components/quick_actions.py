"""
Quick action buttons component for MTL Finder.
"""

import streamlit as st

from config import QUICK_ACTIONS, WELCOME_TIP, TRY_ASKING_HEADER
from state import SessionState


def render_quick_actions() -> None:
    """
    Render quick action buttons for common queries.
    """
    # Only show quick actions if conversation is empty
    # if SessionState.get_message_count() > 0:
    # return

    # Show welcome tip
    st.info(WELCOME_TIP)

    # Show header
    st.markdown(TRY_ASKING_HEADER)

    # Create two columns for buttons
    col1, col2 = st.columns(2)

    # Render buttons from config
    for idx, action in enumerate(QUICK_ACTIONS):
        # Alternate between columns
        col = col1 if idx % 2 == 0 else col2

        with col:
            button_label = f"{action['emoji']} {action['label']}"
            if st.button(button_label, key=f"quick_action_{idx}"):
                # Add message to chat history
                SessionState.add_message("user", action["prompt"])
                # Rerun to process the message
                st.rerun()
    st.divider()
