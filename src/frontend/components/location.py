"""
Location handling component for MTL Finder.
"""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

from state import SessionState


def get_geolocation():
    """
    Request user's geolocation using browser's Geolocation API.

    Returns:
        Dictionary with latitude, longitude, and accuracy if successful,
        or error information if failed.
    """
    # Load the JavaScript file
    assets_dir = Path(__file__).parent.parent / "assets"
    geolocation_js_path = assets_dir / "geolocation.js"

    with open(geolocation_js_path, "r", encoding="utf-8") as f:
        geolocation_js = f.read()

    # Wrap in script tags for components.html()
    html_content = f"<script>{geolocation_js}</script>"

    # Render the component (returns the value sent via postMessage)
    location_data = components.html(html_content, height=0)
    return location_data


def render_location_handler() -> None:
    """
    Handle user location acquisition automatically.

    Requests browser geolocation on page load and stores it in session state.
    Runs silently in the background without displaying any UI.
    """
    # Only attempt to get location if we don't have it yet
    if not SessionState.has_location():
        location_data = get_geolocation()

        # Store location in session state if available
        if location_data and isinstance(location_data, dict):
            if "latitude" in location_data and "longitude" in location_data:
                lat = location_data["latitude"]
                lon = location_data["longitude"]

                # Validate coordinates
                if lat != 0.0 or lon != 0.0:
                    SessionState.set_user_location(latitude=lat, longitude=lon)
                    st.rerun()
            elif "error" in location_data:
                # Location request failed - user will see instructions in sidebar
                pass


def display_location_status() -> None:
    """
    Display the current location status in the sidebar.

    Shows either the current coordinates or instructions for enabling location.
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
        st.caption("To enable location access:")
        st.caption("1. Click the 🔒 icon in your browser's address bar")
        st.caption("2. Allow location access for this site")
        st.caption("3. Refresh the page")
        st.caption("")
        st.caption("⚠️ **Note:** Some laptops don't have GPS hardware. If location doesn't work, you can still specify your starting point in your message.")
