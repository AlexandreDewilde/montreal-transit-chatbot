# Architecture Overview

The MTL Finder is an intelligent travel assistant designed for Montreal, integrating various services to provide comprehensive route planning and information.

## Project Overview
It consists of a FastAPI backend and a Streamlit frontend, both structured for modularity and maintainability. Also there are two docker services running OpenTripPlanner for routing and a Photon geocoder to decode locations from user queries to latitude/longitude coordinates.

MTL Finder combines:
- **Mistral AI** for natural language understanding and responses
- **Photon** for geocoding (converting location names to coordinates)
- **OpenTripPlanner (OTP)** for multi-modal route planning
- **STM GTFS-RT** for real-time transit updates
- **BIXI GBFS** for bike-share availability
- **Open-Meteo** for weather data


## Project Structure

The project is organized into logical components:

```
mistral-project/
├── src/
│   ├── backend/              # FastAPI backend (modular architecture)
│   │   ├── main.py          # FastAPI app initialization and routes
│   │   ├── config.py        # Configuration and logging setup
│   │   ├── models.py        # Pydantic models for API requests/responses
│   │   ├── prompt.txt       # System prompt for Mistral AI agent
│   │   ├── services/        # Business logic layer
│   │   │   ├── session.py   # Session storage management
│   │   │   └── chat.py      # Mistral AI chat orchestration
│   │   ├── tools/           # Mistral AI function calling tools
│   │   │   ├── definitions.py    # Tool schemas for Mistral API
│   │   │   ├── registry.py       # Tool execution registry
│   │   │   ├── routing_tool.py   # Trip planning with OTP
│   │   │   ├── geocoding_tool.py # Location geocoding
│   │   │   ├── weather_tool.py   # Weather data
│   │   │   ├── transit_tool.py   # STM alerts
│   │   │   └── datetime_tool.py  # Current datetime
│   │   └── pyproject.toml   # Backend dependencies (managed by uv)
│   └── frontend/            # Streamlit frontend (componentized)
│       ├── main.py          # UI application entry point
│       ├── config.py        # Frontend configuration
│       ├── state.py         # Session state management
│       ├── api_client.py    # Backend API client
│       ├── components/      # UI components
│       │   ├── chat.py      # Chat interface component
│       │   ├── location.py  # Geolocation component
│       │   ├── quick_actions.py  # Quick action buttons
│       │   └── sidebar.py   # Sidebar component
│       └── pyproject.toml   # Frontend dependencies (managed by uv)
├── otp-data/                # OpenTripPlanner data (gitignored)
│   ├── build-config.json    # OTP build configuration
│   ├── router-config.json   # OTP routing parameters
│   ├── stm.gtfs.zip         # STM transit data
│   └── quebec.osm.pbf       # Quebec street network
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # This file
│   ├── INSTALL.md           # Installation guide
│   └── RUN.md               # Running the application
├── .env                     # Environment variables (gitignored)
├── .env.example             # Environment template
├── docker-compose.otp.yml   # OTP Docker configuration
├── docker-compose.photon.yml # Photon geocoder Docker configuration
├── setup.sh                 # Complete installation script
├── start.sh                 # Start all services (OTP, backend, frontend)
├── stop.sh                  # Stop all services
└── CLAUDE.md                # Development conventions and guidelines
```

## Tools Architecture

The backend implements five Mistral AI function calling tools (defined in `src/backend/tools/definitions.py`, implementations in `src/backend/tools/`):

1.  **`get_current_datetime()`**
    -   Returns current date and time in Montreal timezone (America/Montreal).
    -   Used for planning future trips ("tomorrow at 9am", "in 2 hours").

2.  **`geocode_location(query, limit=1)`**
    -   Uses Photon geocoder (OpenStreetMap-based).
    -   Converts location names/addresses to coordinates.
    -   **Critical**: Always used before `plan_trip` to avoid hardcoded coordinates.
    -   Returns latitude, longitude, and location metadata.

3.  **`get_weather(latitude, longitude)`**
    -   Utilizes the Open-Meteo API.
    -   Returns current weather conditions for a specified location.

4.  **`plan_trip(from_lat, from_lon, to_lat, to_lon, mode, time, arrive_by)`**
    -   Interacts with the OTP GraphQL API.
    -   Supports multiple transportation modes:
        -   `ALL` (default): All modes - transit (bus/metro/REM), walk, and BIXI bike-share
        -   `TRANSIT`: Transit + walk only (no BIXI)
        -   `WALK`: Walking only
        -   `BICYCLE`: BIXI bike-share only
        -   `NO_BUS`: Metro/REM + walk + BIXI (excludes buses)
        -   `NO_METRO`: Bus + walk + BIXI (excludes metro/REM)
    -   Provides up to 5 route options with real-time data and BIXI availability.
    -   Coordinates must come from `geocode_location` tool.
    -   LLM intelligently selects mode based on user preferences (e.g., "avoid buses" → NO_BUS).

5.  **`get_stm_alerts(route_type)`**
    -   Fetches data from the STM GTFS-RT `tripUpdates` endpoint.
    -   Extracts delay information (delays greater than 2 minutes).
    -   Can filter alerts by `metro`, `bus`, or `all`.

## System Prompt Strategy

The AI agent's decision-making process is guided by a specific system prompt strategy:
1.  **Geocode destination**: The agent first converts location names to coordinates using `geocode_location` (NEVER guesses coordinates).
2.  **Check STM alerts**: It checks for any relevant STM service alerts and disruptions.
3.  **Check weather**: It gathers weather information for the relevant locations.
4.  **Plan the trip**: It proceeds to plan the trip using OTP with the geocoded coordinates.
5.  **Present options**: It presents the trip options, considering weather conditions and STM alerts.
6.  **Anti-hallucination**: The agent is strictly instructed to ONLY present routes returned by the API, never inventing bus numbers or schedules.

## Conversation History Architecture

The system maintains complete conversation history including tool interactions:

**Session Store** (`main.py`, `services/session.py`):
- Stores **all messages**: user, assistant, tool calls, and tool results
- Persisted in-memory for the session lifecycle
- Includes timestamps for all messages
- Used for rebuilding complete context on each request

**Mistral Messages** (`services/chat.py`):
- Rebuilt from session store on each request
- Includes system prompt + full conversation history with tool interactions
- Preserves `tool_calls` and `tool_call_id` fields when rebuilding context
- Returns new messages (tool calls + results + final response) to be stored in session

**Why Store Tool Calls?**:
- **Prevents hallucination**: Agent remembers geocoded coordinates instead of inventing them
- **Better context**: Agent can reference previous tool results (e.g., "same location as before")
- **Accurate responses**: Multi-turn conversations maintain factual consistency
- **Trade-off**: Higher token usage, but critical for accuracy with geocoding and routing

**Implementation Flow**:
1. User sends message → stored in session
2. `chat.py` rebuilds full context from session (including previous tool calls)
3. Mistral calls tools → tool call messages tracked
4. Tools return results → tool result messages tracked
5. Mistral responds → final assistant message tracked
6. All new messages (tool calls + results + response) stored back to session

## Frontend Architecture

The frontend is built with Streamlit and follows a componentized architecture:

### Component Structure (`src/frontend/components/`)

1.  **`chat.py`** - Chat Interface Component
    -   Renders message history with user/assistant bubbles
    -   Handles message input and submission
    -   Manages chat UI state and scrolling

2.  **`location.py`** - Geolocation Component
    -   Uses `streamlit-geolocation` to get browser GPS coordinates
    -   Displays current location to user
    -   Automatically includes coordinates in API requests

3.  **`quick_actions.py`** - Quick Action Buttons
    -   Pre-defined common queries (e.g., "Get to Old Montreal")
    -   One-click shortcuts for popular destinations
    -   Improves user experience for common use cases

4.  **`sidebar.py`** - Sidebar Component
    -   Session management (new/clear session)
    -   Application information and links
    -   Settings and configuration options

### Supporting Modules

-   **`api_client.py`** - Backend API Client
    -   Centralized HTTP requests to FastAPI backend
    -   Session management and message history retrieval
    -   Error handling and response parsing

-   **`state.py`** - Session State Management
    -   Manages Streamlit session state
    -   Tracks session ID, messages, and UI state
    -   Provides state initialization and reset functions

-   **`config.py`** - Frontend Configuration
    -   Loads environment variables (API URL, port)
    -   Centralized configuration management

### User Flow

1.  User opens app → Frontend requests browser location
2.  User sends message → Frontend calls backend API with location context
3.  Backend processes message with Mistral AI and tools
4.  Frontend displays streaming response in chat interface
5.  Conversation history persisted in backend session store

## Logging

The backend uses Python's standard logging with **uvicorn's colored formatter** for consistent, readable output:

-   **Colored output**: DEBUG (cyan), INFO (green), WARNING (yellow), ERROR (red), CRITICAL (bright red)
-   **Configurable levels**: Set via `LOG_LEVEL` in `.env` (DEBUG, INFO, WARNING, ERROR, CRITICAL)
-   **Comprehensive coverage**: All tools, endpoints, and services include structured logging
-   **INFO level**: Shows key events (sessions, tool calls, completions, errors)
-   **DEBUG level**: Shows detailed information (arguments, results, internal details)

## Dependencies

### Backend Dependencies (`src/backend/pyproject.toml`)
-   `fastapi`: Web framework for building the API.
-   `uvicorn`: ASGI server for running FastAPI (provides colored logging formatter).
-   `mistralai`: Python client for the Mistral AI API.
-   `requests`: HTTP library for making external API calls.
-   `python-dotenv`: For loading environment variables.
-   `pydantic` & `pydantic-settings`: Data validation and settings management.
-   `gtfs-realtime-bindings`: For parsing GTFS-Realtime data.

### Frontend Dependencies (`src/frontend/pyproject.toml`)
-   `streamlit`: Python library for building interactive web applications.
-   `requests`: HTTP library for making external API calls.

These dependencies are managed and installed using `uv`.
