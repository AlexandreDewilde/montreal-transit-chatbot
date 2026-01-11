# MTL Finder Chat

A real-time chat application built with FastAPI (backend) and Streamlit (frontend), powered by Mistral AI and OpenTripPlanner for intelligent route planning in Montreal.

## Features

- Session-based chat with in-memory storage
- Real-time messaging
- Mistral AI integration with function calling
- OpenTripPlanner integration for multi-modal trip planning
  - Public transit (STM bus and metro)
  - Walking routes
  - Cycling routes
  - Multi-modal combinations
- Weather information integration
- Clean and simple UI with Streamlit
- RESTful API with FastAPI
- Environment variable configuration

## Project Structure

```
mistral-project/
├── .env                       # Environment configuration
├── .env.example               # Example environment file
├── README.md                  # This file
├── run.sh                     # Script to run both backend and frontend
├── setup-otp.sh               # Script to download OTP data
├── start-otp.sh               # Script to start OpenTripPlanner
├── docker-compose.otp.yml     # Docker compose for OTP
├── otp-data/                  # OpenTripPlanner data directory
│   └── graphs/montreal/       # Montreal GTFS and OSM data
├── src/
│   ├── backend/
│   │   ├── main.py            # FastAPI application
│   │   ├── tools.py           # Mistral AI function tools
│   │   ├── pyproject.toml     # Backend dependencies
│   │   └── .venv/             # Backend virtual environment
│   └── frontend/
│       ├── main.py            # Streamlit application
│       ├── pyproject.toml     # Frontend dependencies
│       └── .venv/             # Frontend virtual environment
```

## Prerequisites

- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/) package manager
- Docker and Docker Compose (for OpenTripPlanner)
- Mistral API key

To install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

To install Docker:
- Follow instructions at [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

## Setup

1. Clone the repository:
```bash
cd mistral-project
```

2. Copy the example environment file and add your Mistral API key:
```bash
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY
```

3. Install dependencies (UV will handle this automatically when running the apps):
```bash
# Backend dependencies
cd src/backend
uv sync

# Frontend dependencies
cd ../frontend
uv sync
cd ../..
```

4. Setup OpenTripPlanner (one-time setup):
```bash
# Download GTFS and OSM data for Montreal
./setup-otp.sh
```

5. Start OpenTripPlanner:
```bash
# Start OTP container (takes 5-10 minutes on first run)
./start-otp.sh
```

Wait for OTP to finish building the graph. You'll see messages like "Graph built successfully" in the logs.

## Running the Application

Make sure OpenTripPlanner is running first (see setup step 5 above).

### Option 1: Using the run script (Recommended)

```bash
chmod +x run.sh
./run.sh
```

This will start both the backend and frontend servers.

### Option 2: Manual startup

Start the backend server:
```bash
cd src/backend
uv run uvicorn main:app --reload --port 8000
```

In a new terminal, start the frontend:
```bash
cd src/frontend
uv run streamlit run main.py
```

## API Endpoints

### Backend (FastAPI)

- `GET /` - Health check
- `POST /session` - Create a new chat session
- `GET /session/{session_id}/messages` - Get all messages for a session
- `POST /chat` - Send a message and get a response
- `DELETE /session/{session_id}` - Delete a session
- `GET /health` - Health check endpoint

### Example API Usage

Create a session:
```bash
curl -X POST http://localhost:8000/session
```

Send a message:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!", "session_id": "your-session-id"}'
```

## Configuration

Edit the `.env` file to customize:

- `MISTRAL_API_KEY`: Your Mistral API key (required)
- `MISTRAL_MODEL`: Mistral model to use (default: mistral-small-latest)
- `API_URL`: Backend API URL (default: http://localhost:8000)
- `API_PORT`: Backend API port (default: 8000)
- `FRONTEND_PORT`: Frontend port (default: 8501)

## Available AI Functions

The chatbot can use the following tools:

1. **Weather Information** (`get_weather`)
   - Get current weather for any location
   - Uses Open-Meteo API
   - Example: "What's the weather in Montreal?"

2. **Trip Planning** (`plan_trip`)
   - Plan multi-modal trips in Montreal
   - Supports: public transit (STM), walking, cycling, driving
   - Real-time transit schedules
   - Example: "How do I get from McGill University to Old Montreal by metro?"
   - Example: "Find me a bike route from downtown to Plateau Mont-Royal"

## Development

### Backend Development

The FastAPI backend uses automatic reload:
```bash
cd src/backend
uv run uvicorn main:app --reload
```

Visit http://localhost:8000/docs for the interactive API documentation.

### Frontend Development

Streamlit has built-in hot reload:
```bash
cd src/frontend
uv run streamlit run main.py
```

Visit http://localhost:8501 to access the chat interface.

## OpenTripPlanner Management

### Check OTP Status
```bash
curl http://localhost:8080/otp/routers/default
```

### View OTP Logs
```bash
docker logs -f otp-montreal
```

### Stop OTP
```bash
docker-compose -f docker-compose.otp.yml down
```

### Restart OTP
```bash
docker-compose -f docker-compose.otp.yml restart
```

### Rebuild OTP Graph (after updating GTFS/OSM data)
```bash
docker-compose -f docker-compose.otp.yml down
# Update data in otp-data/graphs/montreal/
docker-compose -f docker-compose.otp.yml up -d
```

## Troubleshooting

### OTP Connection Issues
- Ensure Docker is running: `docker ps`
- Check OTP container status: `docker ps | grep otp-montreal`
- View OTP logs: `docker logs otp-montreal`
- Verify OTP is responding: `curl http://localhost:8080/otp/routers/default`

### Backend Issues
- Verify Mistral API key is set in `.env`
- Check backend logs for errors
- Ensure all dependencies are installed: `cd src/backend && uv sync`

## Future Enhancements

- [x] Integrate AI/LLM for intelligent responses (Mistral AI)
- [x] OpenTripPlanner integration for route planning
- [ ] Add rideshare integration (Uber, Lyft)
- [ ] Add carshare integration (Communauto)
- [ ] Add user authentication
- [ ] Implement persistent storage (database)
- [ ] Add message formatting (markdown, code blocks)
- [ ] Multiple chat rooms
- [ ] WebSocket support for real-time updates
- [ ] Interactive maps for routes
- [ ] Save favorite locations and routes

## License

MIT
