"""
Location handling component for MTL Finder.
"""

import streamlit as st
from streamlit_geolocation import streamlit_geolocation

from state import SessionState


def display_location_status() -> None:
    """
    Display the current location status in the sidebar with a button to request location.

    Shows either the current coordinates or a button to enable location sharing.
    """
    st.header("📍 Your Location")

    if SessionState.has_location():
        location = SessionState.get_user_location()
        if location:
            st.success("✓ Location enabled")
            st.caption(f"📍 {location.latitude:.4f}, {location.longitude:.4f}")
            st.caption("I'll use your location as the starting point for routes!")

            # Button to refresh location
            if st.button("🔄 Update location", use_container_width=True):
                SessionState.clear_location()
                st.rerun()
    else:
        # Use columns to put text and button on same line
        col1, col2 = st.columns([4, 2])

        with col1:
            st.markdown("**📍 Share location:**")

        with col2:
            # Button to request location using streamlit-geolocation
            location_data = streamlit_geolocation()

        # Check if we got location data (outside columns context)
        if location_data:
            if (
                "latitude" in location_data
                and "longitude" in location_data
                and location_data["latitude"]
                and location_data["longitude"]
            ):
                lat = location_data["latitude"]
                lon = location_data["longitude"]

                # Validate coordinates
                if lat != 0.0 or lon != 0.0:
                    SessionState.set_user_location(latitude=lat, longitude=lon)
                    st.rerun()
            else:
                # Location failed or was denied
                st.warning("⚠️ Location sharing is not available on this device or was denied.")

        st.caption("💡 You can also specify your starting point in your message.")
