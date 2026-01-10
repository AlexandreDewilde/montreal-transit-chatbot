from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import uuid

app = FastAPI(title="MTL Finder Chat API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for user sessions
# Key: session_id, Value: list of messages
sessions: Dict[str, List[dict]] = {}


class Message(BaseModel):
    content: str
    session_id: str


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
    """Send a message and get a response"""
    # Initialize session if it doesn't exist
    if message.session_id not in sessions:
        sessions[message.session_id] = []

    # Add user message to session
    user_message = {
        "role": "user",
        "content": message.content,
        "timestamp": datetime.now().isoformat()
    }
    sessions[message.session_id].append(user_message)

    # Generate assistant response (placeholder - can integrate AI later)
    assistant_message = {
        "role": "assistant",
        "content": f"Echo: {message.content}",
        "timestamp": datetime.now().isoformat()
    }
    sessions[message.session_id].append(assistant_message)

    return {
        "session_id": message.session_id,
        "messages": sessions[message.session_id]
    }


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
