# Claude Development Guide - MTL Finder

This document contains important conventions, rules, and project structure information for MTL Finder.

## Project Overview

MTL Finder is an intelligent travel assistant for Montreal that combines:
- **Mistral AI** for natural language understanding and responses
- **Photon** for geocoding (converting location names to coordinates)
- **OpenTripPlanner (OTP)** for multi-modal route planning
- **STM GTFS-RT** for real-time transit updates
- **BIXI GBFS** for bike-share availability
- **Open-Meteo** for weather data

## Git Commit Conventions

All commits must follow this format:

```
<type>(<scope>): <short description>

Format: feat/fix/chore/docs/refactor/test/style(backend/frontend/config): concise description

Examples:
- feat(backend): add STM alerts tool
- fix(frontend): correct location display
- chore: update dependencies
- docs: add API documentation
```

**Important**: Keep commit names very concise - focus on what changed, not why or how.

### Types
- `feat`: New feature
- `fix`: Bug fix
- `chore`: Maintenance tasks
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `style`: Code formatting (no functional changes)

### Scopes
- `backend`: Backend API changes (src/backend/)
- `frontend`: Frontend UI changes (src/frontend/)
- `config`: Configuration files (docker-compose, OTP config, etc.)

### Rules
- **NO** Claude co-author attribution
- Keep commit messages concise and descriptive
- One logical change per commit
- Commit progressively, not all at once

## Project Structure

```
mistral-project/
├── src/
│   ├── backend/              # FastAPI backend
│   │   ├── main.py          # API server with Mistral integration
│   │   ├── config.py        # Configuration and logging setup
│   │   ├── models.py        # Pydantic models
│   │   ├── prompt.txt       # System prompt for Mistral AI
│   │   ├── services/        # Business logic layer
│   │   │   ├── session.py   # Session storage management
│   │   │   └── chat.py      # Mistral AI chat orchestration
│   │   ├── tools/           # Mistral AI function calling tools
│   │   │   ├── definitions.py  # Tool schemas for Mistral API
│   │   │   ├── registry.py     # Tool execution registry
│   │   │   ├── routing_tool.py # Trip planning with OTP
│   │   │   ├── geocoding_tool.py # Location name to coordinates
│   │   │   ├── weather_tool.py   # Weather data
│   │   │   ├── transit_tool.py   # STM alerts
│   │   │   └── datetime_tool.py  # Current datetime
│   │   └── pyproject.toml   # Backend dependencies (managed by uv)
│   └── frontend/            # Streamlit frontend
│       ├── main.py          # UI application
│       ├── components/      # UI components
│       └── pyproject.toml   # Frontend dependencies (managed by uv)
├── otp-data/                # OpenTripPlanner data (gitignored)
│   ├── build-config.json    # OTP build configuration
│   ├── router-config.json   # OTP routing parameters
│   ├── stm.gtfs.zip         # STM transit data (bus & metro)
│   ├── rem.gtfs.zip         # REM transit data (light rail)
│   └── quebec.osm.pbf       # Quebec street network
├── docs/                    # Documentation
├── .env                     # Environment variables (gitignored)
├── .env.example             # Environment template
├── docker-compose.otp.yml   # OTP Docker configuration
├── docker-compose.photon.yml # Photon geocoder Docker configuration
├── setup.sh                 # Complete installation script
├── start.sh                 # Start all services (OTP, backend, frontend)
└── stop.sh                  # Stop all services
```

## Running the Application

### Backend
```bash
cd src/backend
uv run fastapi dev main.py
```
**Important**: Always use `uv run` to ensure dependencies are available!

### Frontend
```bash
cd src/frontend
uv run streamlit run main.py
```

### All Services (Recommended)
```bash
# Complete setup (first time)
./setup.sh

# Start all services (OTP, backend, frontend)
./start.sh

# Stop all services
./stop.sh
```

### Individual Services
```bash
# Start OTP only
docker-compose -f docker-compose.otp.yml up -d

# Start Photon geocoder
docker-compose -f docker-compose.photon.yml up -d
```

## Environment Variables

Required variables in `.env`:

```bash
# Backend
API_URL=http://localhost:8000
API_PORT=8000

# Logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Frontend
FRONTEND_PORT=8501

# Mistral AI
MISTRAL_API_KEY=your_key_here
MISTRAL_MODEL=mistral-small-latest

# STM Real-time API
STM_API_KEY=your_key_here
```

### Logging Levels

The backend uses Python's standard logging with uvicorn's colored formatter:

- **DEBUG**: Very verbose - shows all tool calls, arguments, results, and internal details
- **INFO**: Moderate verbosity - shows key events (new sessions, tool names, errors, completions)
- **WARNING**: Minimal - shows only warnings and errors
- **ERROR**: Errors only
- **CRITICAL**: Critical errors only

**Recommended settings:**
- Development: `LOG_LEVEL=DEBUG` (see everything)
- Production: `LOG_LEVEL=INFO` (balanced logging)
- Troubleshooting: `LOG_LEVEL=DEBUG` (diagnose issues)

### Getting API Keys

**STM API Key**:
1. Register at https://portail.developpeurs.stm.info/apihub
2. Create an application
3. Get the API key (NOT the client_secret)

**Mistral API Key**:
- Get from https://console.mistral.ai/

## OpenTripPlanner Configuration

### Build Configuration (`build-config.json`)

Generated by `setup.sh` with:
- BIXI GBFS updater (60s refresh)
- STM GTFS-RT trip updates (30s refresh)
- STM API key from `.env`

**Important**: API key is inserted via environment variable substitution in `setup.sh`

### Router Configuration (`router-config.json`)

Routing parameters:
- Bike rental enabled (BIXI)
- Walk speed: 1.3 m/s
- Bike speed: 5.0 m/s
- Car speed: 40 km/h
- Max 3 itineraries per request

## Tools Architecture

### Backend Tools (src/backend/tools/)

Five Mistral AI function calling tools (defined in `tools/definitions.py`, implemented across multiple files):

1. **get_current_datetime()**
   - Returns current date and time in Montreal timezone
   - Used for planning future trips ("tomorrow at 9am", "in 2 hours")

2. **geocode_location(query, limit=1)**
   - Uses Photon geocoder (OSM-based)
   - Converts location names/addresses to coordinates
   - **CRITICAL**: Always used before plan_trip to avoid hardcoded coordinates
   - Returns latitude, longitude, and location metadata

3. **get_weather(latitude, longitude)**
   - Uses Open-Meteo API
   - Returns current weather conditions

4. **plan_trip(from_lat, from_lon, to_lat, to_lon, mode)**
   - Uses OTP GraphQL API
   - Modes:
     * `ALL` (default): All modes - transit (bus/metro/REM), walk, BIXI
     * `TRANSIT`: Transit + walk (no BIXI)
     * `WALK`: Walking only
     * `BICYCLE`: BIXI bike-share only
     * `NO_BUS`: Metro/REM + walk + BIXI (excludes buses)
     * `NO_METRO`: Bus + walk + BIXI (excludes metro/REM)
   - Returns up to 5 route options with real-time data
   - **Note**: Coordinates must come from geocode_location
   - LLM selects mode based on user preferences (e.g., "avoid buses" → NO_BUS)

5. **get_stm_alerts(route_type)**
   - Uses STM GTFS-RT tripUpdates endpoint
   - Extracts delays > 2 minutes
   - Filters by: 'metro', 'bus', or 'all'

### System Prompt Strategy

The agent is instructed to:
1. **Geocode destination** using geocode_location (NEVER guess coordinates)
2. Check STM alerts FIRST
3. Check weather
4. Plan the trip using geocoded coordinates
5. Present options considering weather and alerts

## Dependencies

Backend requires:
- fastapi
- uvicorn
- mistralai
- requests
- python-dotenv
- **gtfs-realtime-bindings** (for GTFS-RT parsing)

Frontend requires:
- streamlit
- requests
- streamlit-geolocation

Install with: `cd src/{backend|frontend} && uv sync`

## Common Issues

### "ModuleNotFoundError: No module named 'google.transit'"
**Solution**: Install in backend:
```bash
cd src/backend && uv add gtfs-realtime-bindings
```

### "Invalid API Key" from STM API
**Problem**: Using client_secret instead of API key
**Solution**: Get the actual API key from the STM portal (NOT the OAuth credentials)

### Frontend can't connect to backend
**Problem**: Backend not started with `uv run`
**Solution**: Always use `uv run fastapi dev main.py` in src/backend/

### OTP not showing real-time data
**Problem**: API key not configured in build-config.json
**Solution**: Re-run `./setup.sh` after setting STM_API_KEY in .env

### OTP not showing REM routes
**Problem**: Missing REM GTFS data
**Solution**: The setup.sh script now downloads both STM and REM GTFS feeds. If REM is missing:
```bash
cd otp-data
curl -L "https://exo.quebec/xdata/rem/google_transit.zip" -o rem.gtfs.zip
docker-compose -f docker-compose.otp.yml down
docker-compose -f docker-compose.otp.yml up -d
```

## Testing

To test the complete system:
1. Start all services: `./start.sh`
2. Open browser to http://localhost:8501
3. Allow location access
4. Test a route query

Or start services individually:
1. Start OTP: `docker-compose -f docker-compose.otp.yml up -d`
2. Start backend: `cd src/backend && uv run fastapi dev main.py`
3. Start frontend: `cd src/frontend && uv run streamlit run main.py`

## Todo List Tasks

Current pending tasks:
1. Test complete system with BIXI and STM alerts
2. Perform fresh deployment from scratch
3. Research hosting solution options

## Montreal Specific Data

### STM Metro Lines
- Line 1 (Green): Angrignon ↔ Honoré-Beaugrand
- Line 2 (Orange): Côte-Vertu ↔ Montmorency
- Line 4 (Yellow): Berri-UQAM ↔ Longueuil
- Line 5 (Blue): Snowdon ↔ Saint-Michel

### Common Destinations (Lat, Lon)
- Old Montreal: 45.5048, -73.5540
- McGill University: 45.5048, -73.5762
- Mont-Royal Park: 45.5048, -73.5874
- Plateau Mont-Royal: 45.5262, -73.5782
- Jean-Talon Market: 45.5356, -73.6135
- Olympic Stadium: 45.5579, -73.5516

## Additional Resources

- [STM Developer Portal](https://www.stm.info/en/about/developers)
- [OTP Documentation](http://docs.opentripplanner.org/)
- [Mistral AI Docs](https://docs.mistral.ai/)
- [GTFS-RT Specification](https://gtfs.org/realtime/)
