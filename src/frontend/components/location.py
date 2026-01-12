"""
Location handling component for MTL Finder.
"""
import streamlit as st
from streamlit_geolocation import streamlit_geolocation

from state import SessionState


def render_location_handler() -> None:
    """
    Handle user location acquisition.

    Uses streamlit_geolocation to request and store user's location.
    Only requests location once per session.
    """
    # Only attempt to get location if we don't have it yet
    if not SessionState.has_location():
        location = streamlit_geolocation()

        # Store location in session state if available
        if location and location.get("latitude") is not None:
            SessionState.set_user_location(
                latitude=location["latitude"],
                longitude=location["longitude"],
            )
            # Rerun to update UI
            st.rerun()


def display_location_status() -> None:
    """
    Display the current location status in the sidebar.

    Shows either the current coordinates or a message about enabling location.
    """
    st.header("📍 Your Location")

    if SessionState.has_location():
        location = SessionState.get_user_location()
        if location:
            st.success("✓ Location enabled")
            st.caption(f"📍 {location.latitude:.4f}, {location.longitude:.4f}")
            st.caption("I'll use your location as the starting point for routes!")
    else:
        st.warning("⚠️ Location not available")
        st.caption("Please allow browser location access to:")
        st.caption("• Get weather for your area")
        st.caption("• Use your location as trip starting point")
