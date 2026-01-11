# Architecture Overview

The MTL Finder is an intelligent travel assistant designed for Montreal, integrating various services to provide comprehensive route planning and information.

## Project Overview

MTL Finder combines:
- **Mistral AI** for natural language understanding and responses
- **OpenTripPlanner (OTP)** for multi-modal route planning
- **STM GTFS-RT** for real-time transit updates
- **BIXI GBFS** for bike-share availability
- **Open-Meteo** for weather data

## Project Structure

The project is organized into logical components:

```
mistral-project/
├── src/
│   ├── backend/              # FastAPI backend
│   │   ├── main.py          # API server with Mistral integration
│   │   ├── tools.py         # Mistral AI function calling tools
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
├── .env.example             # Environment template
├── docker-compose.otp.yml   # Docker compose for OTP
├── setup.sh                 # Complete installation script
├── start.sh                 # Script to start backend and frontend
├── stop.sh                  # Script to stop services
├── start-otp.sh             # Script to start OpenTripPlanner
├── restart-otp.sh           # Script to restart OpenTripPlanner
└── CLAUDE.md                # Development conventions and guidelines (to be moved or integrated)
```

## Tools Architecture

The backend (`src/backend/tools.py`) implements three key Mistral AI function calling tools:

1.  **`get_weather(latitude, longitude)`**
    -   Utilizes the Open-Meteo API.
    -   Returns current weather conditions for a specified location.

2.  **`plan_trip(from_lat, from_lon, to_lat, to_lon, mode)`**
    -   Interacts with the OTP GraphQL API.
    -   Supports various modes: `TRANSIT,WALK`, `WALK`, `BICYCLE`, `CAR`.
    -   Provides up to 3 route options, incorporating real-time data.

3.  **`get_stm_alerts(route_type)`**
    -   Fetches data from the STM GTFS-RT `tripUpdates` endpoint.
    -   Extracts delay information (delays greater than 2 minutes).
    -   Can filter alerts by `metro`, `bus`, or `all`.

## System Prompt Strategy

The AI agent's decision-making process is guided by a specific system prompt strategy:
1.  **Prioritize STM alerts**: The agent first checks for any relevant STM alerts.
2.  **Check weather**: It then gathers weather information for the relevant locations.
3.  **Plan the trip**: Subsequently, it proceeds to plan the trip using OTP.
4.  **Present options**: Finally, it presents the trip options, taking into account both weather conditions and any existing STM alerts.

## Dependencies

### Backend Dependencies (`src/backend/pyproject.toml`)
-   `fastapi`: Web framework for building the API.
-   `uvicorn`: ASGI server for running FastAPI.
-   `mistralai`: Python client for the Mistral AI API.
-   `requests`: HTTP library for making external API calls.
-   `python-dotenv`: For loading environment variables.
-   `gtfs-realtime-bindings`: For parsing GTFS-Realtime data.

### Frontend Dependencies (`src/frontend/pyproject.toml`)
-   `streamlit`: Python library for building interactive web applications.
-   `requests`: HTTP library for making external API calls.
-   `streamlit-geolocation`: For integrating geolocation features.

These dependencies are managed and installed using `uv`.
