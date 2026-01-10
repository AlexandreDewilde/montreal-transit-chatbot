# MTL Finder Chat

A real-time chat application built with FastAPI (backend) and Streamlit (frontend), using UV for environment management.

## Features

- Session-based chat with in-memory storage
- Real-time messaging
- Clean and simple UI with Streamlit
- RESTful API with FastAPI
- Environment variable configuration

## Project Structure

```
mistral-project/
├── .env                    # Environment configuration
├── .env.example            # Example environment file
├── README.md               # This file
├── run.sh                  # Script to run both backend and frontend
├── src/
│   ├── backend/
│   │   ├── main.py         # FastAPI application
│   │   ├── pyproject.toml  # Backend dependencies
│   │   └── .venv/          # Backend virtual environment
│   └── frontend/
│       ├── main.py         # Streamlit application
│       ├── pyproject.toml  # Frontend dependencies
│       └── .venv/          # Frontend virtual environment
```

## Prerequisites

- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/) package manager

To install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

1. Clone the repository:
```bash
cd mistral-project
```

2. Copy the example environment file:
```bash
cp .env.example .env
```

3. Install dependencies (UV will handle this automatically when running the apps):
```bash
# Backend dependencies
cd src/backend
uv sync

# Frontend dependencies
cd ../frontend
uv sync
```

## Running the Application

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

- `API_URL`: Backend API URL (default: http://localhost:8000)
- `API_PORT`: Backend API port (default: 8000)
- `FRONTEND_PORT`: Frontend port (default: 8501)

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

## Future Enhancements

- [ ] Integrate AI/LLM for intelligent responses
- [ ] Add user authentication
- [ ] Implement persistent storage (database)
- [ ] Add message formatting (markdown, code blocks)
- [ ] File upload support
- [ ] Multiple chat rooms
- [ ] WebSocket support for real-time updates

## License

MIT
