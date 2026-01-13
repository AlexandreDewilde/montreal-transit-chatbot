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
│   │   ├── tools.py         # Mistral AI function calling tools
│   │   ├── prompt.txt       # System prompt for Mistral AI agent
│   │   ├── services/        # Business logic layer
│   │   │   ├── session.py   # Session storage management
│   │   │   └── chat.py      # Mistral AI chat orchestration
│   │   └── pyproject.toml   # Backend dependencies (managed by uv)
│   └── frontend/            # Streamlit frontend
│       ├── main.py          # UI with geolocation
│       └── pyproject.toml   # Frontend dependencies (managed by uv)
├── otp-data/                # OpenTripPlanner data (gitignored)
│   └── graphs/montreal/
│       ├── build-config.json    # OTP build configuration
│       ├── router-config.json   # OTP routing parameters
│       ├── stm.gtfs.zip         # STM transit data
│       └── quebec.osm.pbf       # Quebec street network
├── docs/                    # Documentation
│   └── ARCHITECTURE.md      # This file
├── .env.example             # Environment template
├── docker-compose.otp.yml   # Docker compose for OTP
├── setup.sh                 # Complete installation script
├── start.sh                 # Script to start backend and frontend
├── stop.sh                  # Script to stop services
├── start-otp.sh             # Script to start OpenTripPlanner
├── restart-otp.sh           # Script to restart OpenTripPlanner
└── CLAUDE.md                # Development conventions and guidelines
```

## Tools Architecture

The backend (`src/backend/tools.py`) implements five Mistral AI function calling tools:

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
    -   Supports various modes: `TRANSIT,WALK`, `WALK`, `BICYCLE` (includes BIXI bike-share), `TRANSIT`.
    -   Provides up to 5 route options with real-time data and BIXI availability.
    -   Coordinates must come from `geocode_location` tool.

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

The system maintains conversation state at two levels:

**Session Store** (`main.py`):
- Stores only user/assistant messages (final outputs)
- Persisted in-memory for the session lifecycle
- Used for displaying conversation history to users

**Mistral Messages** (`chat.py`):
- Ephemeral: rebuilt from session store on each request
- Includes system prompt, user messages, and **current turn's** tool calls/results
- Previous tool calls are **not persisted** between turns

**Trade-off Discussion**:
- **Current approach**: Minimal token usage, loses tool call history between turns
- **Full history**: Store all tool calls/results in session → better context, avoid redundant calls, but higher token costs
- **Hybrid**: Keep last N tool calls or summarize previous tool usage
- **Current choice**: Optimize for cost over context preservation

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
