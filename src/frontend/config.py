"""
Configuration and constants for MTL Finder frontend.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from project root
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TIMEOUT = 30  # seconds
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 1  # seconds

# Page Configuration
PAGE_TITLE = "MTL Finder Chat"
PAGE_ICON = "💬"
LAYOUT = "centered"

# App Metadata
APP_TITLE = "🗺️ MTL Finder"
APP_CAPTION = "Your intelligent travel assistant for Montreal - powered by Mistral AI & OpenTripPlanner"

# Popular Montreal Destinations (will be geocoded dynamically)
DESTINATIONS: List[str] = [
    "Old Montreal",
    "Mont-Royal Park",
    "McGill University",
    "Plateau Mont-Royal",
    "Jean-Talon Market",
    "Olympic Stadium",
    "Atwater Market",
]

# Quick Action Buttons
QUICK_ACTIONS = [
    {
        "emoji": "🚇",
        "label": "How do I get to Old Montreal?",
        "prompt": "How do I get to Old Montreal?",
    },
    {
        "emoji": "🚲",
        "label": "Best bike route to Plateau?",
        "prompt": "What's the best bike route to Plateau Mont-Royal?",
    },
    {
        "emoji": "🌤️",
        "label": "What's the weather?",
        "prompt": "What's the weather like right now?",
    },
    {
        "emoji": "🏛️",
        "label": "Get to McGill University",
        "prompt": "How do I get to McGill University?",
    },
]

# UI Messages
WELCOME_TIP = "💡 **Tip:** I can help you plan trips using metro, bus, bike, or walking. I'll check the weather to recommend the best option!"
TRY_ASKING_HEADER = "**Try asking:**"
LOCATION_ENABLED_MSG = "✓ Location enabled"
LOCATION_DISABLED_MSG = "⚠️ Location not available"
LOCATION_HELP_TEXT = """Please allow browser location access to:
• Get weather for your area
• Use your location as trip starting point"""
LOCATION_USE_MSG = "I'll use your location as the starting point for routes!"

# Sidebar Sections
ABOUT_TEXT = """**MTL Finder** uses:
• Mistral AI for intelligent responses
• OpenTripPlanner for route planning
• Photon (OSM) for geocoding
• Real-time STM transit data & BIXI bike-share
• Open-Meteo for weather info"""

GITHUB_URL = "https://github.com/AlexandreDewilde/montreal-transit-chatbot"

# Error Messages
ERROR_API_CONNECTION = "Error connecting to API: {error}"
ERROR_API_STATUS = "Error: API returned status code {status}"
ERROR_SESSION_CREATE = "Could not create session with API, using local session"

# Chat Configuration
CHAT_INPUT_PLACEHOLDER = "What would you like to know?"
THINKING_MESSAGE = "Thinking..."
