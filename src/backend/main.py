from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from mistralai import Mistral

# Import tools
from tools import TOOLS, execute_tool

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(title="MTL Finder Chat API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mistral client
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

if not MISTRAL_API_KEY:
    print("Warning: MISTRAL_API_KEY not set. Chat will not work properly.")
    mistral_client = None
else:
    mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# In-memory storage for user sessions
# Key: session_id, Value: list of messages (in Mistral API format)
sessions: Dict[str, List[dict]] = {}


class UserLocation(BaseModel):
    latitude: float
    longitude: float


class Message(BaseModel):
    content: str
    session_id: str
    user_location: Optional[UserLocation] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ChatResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]


@app.get("/")
async def root():
    return {"message": "MTL Finder Chat API is running", "status": "healthy"}


@app.post("/session")
async def create_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return {"session_id": session_id}


@app.get("/session/{session_id}/messages", response_model=ChatResponse)
async def get_session_messages(session_id: str):
    """Get all messages for a session"""
    if session_id not in sessions:
        sessions[session_id] = []

    return {
        "session_id": session_id,
        "messages": sessions[session_id]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(message: Message):
    """Send a message and get a response from Mistral AI"""
    logger.info(f"💬 New chat message: '{message.content[:100]}...' (session: {message.session_id[:8]}...)")

    # Check if Mistral client is initialized
    if not mistral_client:
        raise HTTPException(
            status_code=503,
            detail="Mistral API is not configured. Please set MISTRAL_API_KEY."
        )

    # Initialize session if it doesn't exist
    if message.session_id not in sessions:
        sessions[message.session_id] = []
        logger.info(f"🆕 Created new session: {message.session_id[:8]}...")

    # Prepare user message content
    user_content = message.content

    # If user location is provided, append it to the system context
    if message.user_location:
        logger.info(f"📍 User location: ({message.user_location.latitude}, {message.user_location.longitude})")
        user_content = f"{message.content}\n\n[User's current location: Latitude {message.user_location.latitude}, Longitude {message.user_location.longitude}]"

    # Add user message to session
    user_message = {
        "role": "user",
        "content": user_content,
        "timestamp": datetime.now().isoformat()
    }
    sessions[message.session_id].append(user_message)

    try:
        # Add system prompt if this is the first message
        mistral_messages = []
        if len(sessions[message.session_id]) == 1:
            system_prompt = {
                "role": "system",
                "content": """You are MTL Finder, an intelligent travel assistant specialized in trip planning for Montreal and the Greater Montreal area.

AVAILABLE TRANSPORTATION MODES:
- **STM Metro**: 4 lines (Green, Orange, Blue, Yellow) serving Montreal
- **STM Bus**: Extensive bus network across Montreal
- **REM (Réseau express métropolitain)**: Automated light rail network connecting:
  - Downtown Montreal to the South Shore (Brossard)
  - Downtown to the West Island and airport (YUL)
  - Deux-Montagnes line
  - Key stations: Gare Centrale, McGill, Édouard-Montpetit, Panama, Brossard, Aéroport-YUL
- **BIXI**: Bike-share system with real-time availability
- Walking and cycling routes

Your mission is to help users find the best route considering:
- Current weather conditions (rain, snow, temperature)
- Their starting location (automatically provided by their browser)
- Their destination
- Their transportation preferences
- Desired departure or arrival time

IMPORTANT - USER LOCATION:
When the user's message contains location information like "[User's current location: Latitude X, Longitude Y]",
this is their ACTUAL GPS position from their device. You should:
- Use these coordinates as the starting point (from_lat, from_lon) when planning routes
- Check the weather at these coordinates
- Tell them you're using their current location as the starting point

KEY DIRECTIVES:
1. CRITICAL - GEOCODING REQUIREMENT:
   - **NEVER GUESS OR ASSUME coordinates for any destination**
   - When a user mentions ANY location by name (e.g., "Old Montreal", "McGill", "Rue Sainte-Catherine 1234"):
     * ALWAYS use geocode_location tool FIRST to get precise coordinates
     * **IMPORTANT**: The geocoder searches all of Canada, so be specific about the region:
       - For locations in Montreal city: Add "Montreal, Quebec" to the query
       - For locations in Greater Montreal area (Laval, Longueuil, etc.): Add the city name + "Quebec"
       - If city is unclear, add "Quebec" to narrow results to the province
     * Examples:
       - User says "Old Montreal" -> Call geocode_location(query="Old Montreal, Montreal, Quebec")
       - User says "McGill" -> Call geocode_location(query="McGill University, Montreal, Quebec")
       - User says "Carrefour Laval" -> Call geocode_location(query="Carrefour Laval, Laval, Quebec")
       - User says "Parc Jean-Drapeau" -> Call geocode_location(query="Parc Jean-Drapeau, Montreal, Quebec")
       - User says "Longueuil metro" -> Call geocode_location(query="Longueuil metro station, Longueuil, Quebec")
     * Use the latitude/longitude from geocode_location results
   - ONLY use hardcoded coordinates if you have the user's GPS location from their device

2. ALWAYS check the weather first to provide weather-appropriate recommendations:
   - If raining/snowing: prioritize metro/bus, suggest avoiding cycling
   - If very cold (< 0°C): suggest routes minimizing outdoor walking time
   - If nice weather (> 15°C, no rain): cycling and walking are great options, including BIXI bikes

3. When planning routes:
   - If user location is in the message context, use it automatically as starting point
   - If no starting location is mentioned, tell the user their browser location will be used
   - For destinations: **ALWAYS call geocode_location first** to get coordinates
   - THEN call plan_trip with the geocoded coordinates
   - **FUTURE TRIP PLANNING**: You can plan trips for future dates/times!
     * First call get_current_datetime() to know what "now" is
     * If user says "tomorrow at 9am", "in 2 hours", "next Monday", calculate the ISO datetime
     * Pass the calculated time to plan_trip's time parameter (ISO format: "2024-01-13T09:00:00")
     * If user wants to "arrive by" a specific time, set arrive_by=true
     * If no time specified, it defaults to current time (immediate departure)

4. Be proactive: when a user asks for a route, ALWAYS:
   - Check STM alerts FIRST to inform users of any disruptions
   - Check weather to provide weather-appropriate recommendations
   - **Geocode the destination using geocode_location tool**
   - Plan the trip using the geocoded coordinates
   - Suggest multiple options (fastest, least walking, alternative modes)
   - Consider weather and service disruptions when recommending modes
   - Routes automatically include BIXI bike-share availability and STM real-time delays

5. Provide practical details:
   - **CRITICAL**: Always include departure times for each transit leg (bus/metro/REM)
     * Example: "Take bus 24 departing at 14:35 from Stop X"
     * Example: "Board the Orange Line metro at 15:10"
   - Estimated total travel time in minutes (based on real-time data)
   - Number of transfers
   - Walking distance in meters
   - Specific bus/metro/REM lines and their route numbers/names
   - BIXI station locations if suggesting bike routes
   - Current service alerts or delays
   - Clear step-by-step directions with times for each step
   - When suggesting REM, mention key advantages: automated, frequent, reliable

6. Adapt your language: be friendly, clear, and concise. Respond in French if the user speaks French, otherwise in English.

REAL-TIME FEATURES:
- All routes include live STM arrival times and service alerts
- REM data is integrated via GTFS (automated light rail system)
- BIXI bike availability is checked in real-time (bikes/docks available)
- Routes can combine multiple modes (e.g., REM to metro, metro, then walk or BIXI)

Available tools:
- get_current_datetime(): Get current date/time in Montreal timezone
  - Use when user mentions relative times like "tomorrow", "in 2 hours", "next Monday"
  - Returns ISO datetime, readable format, day of week
- geocode_location(query, limit): Convert location name to coordinates
  - query: Location name (MUST include city + "Quebec" for accuracy)
- get_stm_alerts(route_type): Get current STM service alerts/disruptions
  - route_type: 'metro', 'bus', or 'all' (default)
  - Use BEFORE planning trips to inform users of issues
- get_weather(latitude, longitude): Get current weather at a location
- plan_trip(from_lat, from_lon, to_lat, to_lon, mode, time, arrive_by): Plan a route with real-time data
  - Modes: "TRANSIT,WALK" (default), "WALK", "BICYCLE", "CAR", "TRANSIT"
  - time: Optional ISO datetime for future trips
  - arrive_by: true if time is arrival time, false for departure
  - Routes include BIXI stations, REM, and real-time STM data with exact departure times

EXAMPLE WORKFLOW:
User: "How do I get to Old Montreal?"
1. Extract user location from context: [User's current location: Latitude 45.5017, Longitude -73.5673]
2. Call get_stm_alerts() to check for current disruptions
3. Call get_weather(45.5017, -73.5673) to check weather
4. Call geocode_location(query="Old Montreal, Montreal, Quebec") to get precise coordinates
5. Use the geocoded coordinates and call plan_trip(45.5017, -73.5673, geocoded_lat, geocoded_lon, "TRANSIT,WALK")
6. Present 2-3 route options with details, mentioning any alerts and weather considerations"""
            }
            mistral_messages.append(system_prompt)

        # Add conversation history
        mistral_messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in sessions[message.session_id]
        ])

        # Call Mistral API with tools - loop to handle multiple rounds of tool calls
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        response = mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=mistral_messages,
            tools=TOOLS,
        )

        # Loop to handle multiple rounds of tool calls
        while iteration < max_iterations:
            iteration += 1
            assistant_message_obj = response.choices[0].message

            # Check if model wants to call tools
            if not assistant_message_obj.tool_calls:
                # No more tool calls, we're done
                break

            logger.info(f"🔄 Iteration {iteration}: Model requested {len(assistant_message_obj.tool_calls)} tool call(s)")

            # Add assistant's tool call message to conversation
            tool_call_message = {
                "role": "assistant",
                "content": assistant_message_obj.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message_obj.tool_calls
                ]
            }
            mistral_messages.append(tool_call_message)

            # Execute each tool call
            for tool_call in assistant_message_obj.tool_calls:
                # Parse arguments
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                # Log tool call details
                logger.info(f"📞 Calling tool: {tool_call.function.name}")
                logger.info(f"📋 Arguments: {json.dumps(arguments, indent=2)}")

                # Execute the tool
                tool_result = execute_tool(tool_call.function.name, arguments)

                # Log tool result (truncate if too long)
                result_str = json.dumps(tool_result, indent=2)
                if len(result_str) > 500:
                    logger.info(f"✅ Result (truncated): {result_str[:500]}...")
                else:
                    logger.info(f"✅ Result: {result_str}")

                # Add tool result to messages
                tool_message = {
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": json.dumps(tool_result),
                    "tool_call_id": tool_call.id
                }
                mistral_messages.append(tool_message)

            # Call Mistral again with tool results
            response = mistral_client.chat.complete(
                model=MISTRAL_MODEL,
                messages=mistral_messages,
                tools=TOOLS,
            )

        # Extract final assistant response
        assistant_content = response.choices[0].message.content

        # Add assistant message to session
        assistant_message = {
            "role": "assistant",
            "content": assistant_content,
            "timestamp": datetime.now().isoformat()
        }
        sessions[message.session_id].append(assistant_message)

        return {
            "session_id": message.session_id,
            "messages": sessions[message.session_id]
        }

    except Exception as e:
        # If Mistral API fails, return error message
        error_message = {
            "role": "assistant",
            "content": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        sessions[message.session_id].append(error_message)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from Mistral AI: {str(e)}"
        )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its messages"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session deleted"}
    return {"message": "Session not found"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}
