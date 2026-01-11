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
    except requests.exceptions.RequestException:
        st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_location" not in st.session_state:
    st.session_state.user_location = None

if "location_requested" not in st.session_state:
    st.session_state.location_requested = False

# App title and description
st.title("🗺️ MTL Finder")
st.caption(
    "Your intelligent travel assistant for Montreal - powered by Mistral AI & OpenTripPlanner"
)

# Get user location only if not already obtained
if st.session_state.user_location is None:
    location = streamlit_geolocation()

    # Store location in session state if available
    if location and location.get("latitude") is not None:
        st.session_state.user_location = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
        }
        st.rerun()

# Show quick actions if no messages yet
if len(st.session_state.messages) == 0:
    st.info(
        "💡 **Tip:** I can help you plan trips using metro, bus, bike, or walking. I'll check the weather to recommend the best option!"
    )

    st.markdown("**Try asking:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚇 How do I get to Old Montreal?"):
            st.session_state.messages.append(
                {"role": "user", "content": "How do I get to Old Montreal?"}
            )
            st.rerun()
        if st.button("🚲 Best bike route to Plateau?"):
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": "What's the best bike route to Plateau Mont-Royal?",
                }
            )
            st.rerun()
    with col2:
        if st.button("🌤️ What's the weather?"):
            st.session_state.messages.append(
                {"role": "user", "content": "What's the weather like right now?"}
            )
            st.rerun()
        if st.button("🏛️ Get to McGill University"):
            st.session_state.messages.append(
                {"role": "user", "content": "How do I get to McGill University?"}
            )
            st.rerun()

    st.divider()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input or button click
prompt = None
send_to_api = False

if user_input := st.chat_input("What would you like to know?"):
    prompt = user_input
    st.session_state.messages.append({"role": "user", "content": prompt})
    send_to_api = True
elif (
    len(st.session_state.messages) > 0
    and st.session_state.messages[-1]["role"] == "user"
):
    # Check if last message is from user (button click) and hasn't been processed
    if "last_processed_idx" not in st.session_state:
        st.session_state.last_processed_idx = -1
    current_idx = len(st.session_state.messages) - 1
    if current_idx > st.session_state.last_processed_idx:
        prompt = st.session_state.messages[-1]["content"]
        st.session_state.last_processed_idx = current_idx
        send_to_api = True

if send_to_api and prompt:
    # Send message to API and get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Prepare request payload
                payload = {"content": prompt, "session_id": st.session_state.session_id}

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
                        st.rerun()
                else:
                    error_msg = (
                        f"Error: API returned status code {response.status_code}"
                    )
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
                    st.rerun()
            except Exception as e:
                error_msg = f"Error connecting to API: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                st.rerun()

# Sidebar
with st.sidebar:
    st.header("📍 Your Location")
    if st.session_state.user_location:
        lat = st.session_state.user_location["latitude"]
        lon = st.session_state.user_location["longitude"]
        st.success("✓ Location enabled")
        st.caption(f"📍 {lat:.4f}, {lon:.4f}")
        st.caption("I'll use your location as the starting point for routes!")
    else:
        st.warning("⚠️ Location not available")
        st.caption("Please allow browser location access to:")
        st.caption("• Get weather for your area")
        st.caption("• Use your location as trip starting point")

    st.divider()

    st.header("🎯 Popular Destinations")
    destinations = {
        "Old Montreal": (45.5048, -73.5540),
        "Mont-Royal Park": (45.5048, -73.5874),
        "McGill University": (45.5048, -73.5762),
        "Plateau Mont-Royal": (45.5262, -73.5782),
        "Jean-Talon Market": (45.5356, -73.6135),
        "Olympic Stadium": (45.5579, -73.5516),
        "Atwater Market": (45.4771, -73.5818),
    }

    selected_dest = st.selectbox(
        "Quick destination select:",
        [""] + list(destinations.keys()),
        format_func=lambda x: "Choose a destination..." if x == "" else x,
    )

    if selected_dest:
        if st.button(f"🗺️ Get directions to {selected_dest}"):
            prompt = f"How do I get to {selected_dest}?"
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

    st.divider()

    st.header("ℹ️ About")
    st.caption("**MTL Finder** uses:")
    st.caption("• Mistral AI for intelligent responses")
    st.caption("• OpenTripPlanner for route planning")
    st.caption("• Real-time STM transit data")
    st.caption("• Open-Meteo for weather info")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 New Session"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
