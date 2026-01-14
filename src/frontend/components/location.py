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
        col1, col2 = st.columns([6, 2])

        with col1:
            st.markdown("**📍 Share location:**")

        with col2:
            # Button to request location using streamlit-geolocation
            location_data = streamlit_geolocation()

        # Check if we got location data (outside columns context)
        if (
            location_data
            and "latitude" in location_data
            and "longitude" in location_data
        ):
            lat = location_data["latitude"]
            lon = location_data["longitude"]

            # Validate coordinates
            if lat and lon and (lat != 0.0 or lon != 0.0):
                st.write(f"🔍 DEBUG: Got location - {lat:.4f}, {lon:.4f}")
                SessionState.set_user_location(latitude=lat, longitude=lon)
                st.success(f"✅ Location saved: {lat:.4f}, {lon:.4f}")
                st.rerun()

        st.caption("💡 You can also specify your starting point in your message.")
