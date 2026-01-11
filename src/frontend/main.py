import streamlit as st
import requests
import uuid
import os
from dotenv import load_dotenv
from pathlib import Path
from streamlit_geolocation import streamlit_geolocation

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# API configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(page_title="MTL Finder Chat", page_icon="💬", layout="centered")

# Initialize session state
if "session_id" not in st.session_state:
    # Create a new session
    try:
        response = requests.post(f"{API_URL}/session")
        if response.status_code == 200:
            st.session_state.session_id = response.json()["session_id"]
        else:
            st.session_state.session_id = str(uuid.uuid4())
    except:
        st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_location" not in st.session_state:
    st.session_state.user_location = None

if "location_requested" not in st.session_state:
    st.session_state.location_requested = False

# App title
st.title("💬 MTL Finder Chat")

# Get user location only if not already obtained
if st.session_state.user_location is None:
    location = streamlit_geolocation()

    # Store location in session state if available
    if location and location.get("latitude") is not None:
        st.session_state.user_location = {
            "latitude": location["latitude"],
            "longitude": location["longitude"]
        }
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send message to API and get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Prepare request payload
                payload = {
                    "content": prompt,
                    "session_id": st.session_state.session_id
                }

                # Add user location if available
                if st.session_state.user_location:
                    payload["user_location"] = st.session_state.user_location

                response = requests.post(
                    f"{API_URL}/chat",
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    # Get the last assistant message
                    assistant_messages = [
                        msg for msg in data["messages"] if msg["role"] == "assistant"
                    ]
                    if assistant_messages:
                        assistant_response = assistant_messages[-1]["content"]
                        st.markdown(assistant_response)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": assistant_response}
                        )
                else:
                    error_msg = (
                        f"Error: API returned status code {response.status_code}"
                    )
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
            except Exception as e:
                error_msg = f"Error connecting to API: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

# Sidebar
with st.sidebar:
    st.header("Session Info")
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")

    st.divider()

    st.header("Location")
    if st.session_state.user_location:
        lat = st.session_state.user_location["latitude"]
        lon = st.session_state.user_location["longitude"]
        st.success("Location detected")
        st.caption(f"Lat: {lat:.4f}")
        st.caption(f"Lon: {lon:.4f}")
    else:
        st.info("Location not available")
        st.caption("Allow browser location access to enable weather features")

    st.divider()

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
