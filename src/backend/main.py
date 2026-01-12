from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
from pathlib import Path

from mistralai import Mistral

from config import get_settings, setup_logging, get_logger
from models import Message, ChatResponse
from services.session import SessionStore
from services.chat import ChatService

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="MTL Finder Chat API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

# Initialize Mistral client
if not settings.mistral_api_key:
    logger.warning("MISTRAL_API_KEY not set. Chat will not work properly.")
    mistral_client = None
else:
    mistral_client = Mistral(api_key=settings.mistral_api_key)

# Initialize session store (singleton)
session_store = SessionStore()

# Initialize chat service
current_folder = Path(__file__).parent
prompt_file_path = current_folder / "prompt.txt"

chat_service = None
if mistral_client:
    chat_service = ChatService(
        mistral_client=mistral_client,
        model=settings.mistral_model,
        max_iterations=settings.max_chat_iterations,
        prompt_file_path=prompt_file_path,
        logger=logger,
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MTL Finder Chat API is running", "status": "healthy"}


@app.post("/session")
async def create_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session_store.create_session(session_id)
    return {"session_id": session_id}


@app.get("/session/{session_id}/messages", response_model=ChatResponse)
async def get_session_messages(session_id: str):
    """Get all messages for a session"""
    messages = session_store.get_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@app.post("/chat", response_model=ChatResponse)
async def chat(message: Message):
    """Send a message and get a response from Mistral AI"""
    logger.info(
        f"💬 New chat message: '{message.content[:100]}...' (session: {message.session_id[:8]}...)"
    )

    # Check if Mistral client is initialized
    if not mistral_client or not chat_service:
        raise HTTPException(
            status_code=503,
            detail="Mistral API is not configured. Please set MISTRAL_API_KEY.",
        )

    # Initialize session if it doesn't exist
    if not session_store.session_exists(message.session_id):
        session_store.create_session(message.session_id)
        logger.info(f"🆕 Created new session: {message.session_id[:8]}...")

    # Prepare user message content
    user_content = message.content

    # If user location is provided, append it to the message content
    if message.user_location:
        logger.info(
            f"📍 User location: ({message.user_location.latitude}, {message.user_location.longitude})"
        )
        user_content = f"{message.content}\n\n[User's current location: Latitude {message.user_location.latitude}, Longitude {message.user_location.longitude}]"

    # Add user message to session
    user_message = {
        "role": "user",
        "content": user_content,
        "timestamp": datetime.now().isoformat(),
    }
    session_store.add_message(message.session_id, user_message)

    try:
        # Get session messages
        session_messages = session_store.get_messages(message.session_id)

        # Process message through chat service
        assistant_content = chat_service.process_message(user_content, session_messages)

        # Add assistant message to session
        assistant_message = {
            "role": "assistant",
            "content": assistant_content,
            "timestamp": datetime.now().isoformat(),
        }
        session_store.add_message(message.session_id, assistant_message)

        # Return all messages
        all_messages = session_store.get_messages(message.session_id)
        return {
            "session_id": message.session_id,
            "messages": all_messages,
        }

    except Exception as e:
        # If Mistral API fails, return error message
        error_message = {
            "role": "assistant",
            "content": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }
        session_store.add_message(message.session_id, error_message)

        raise HTTPException(
            status_code=500, detail=f"Failed to get response from Mistral AI: {str(e)}"
        )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its messages"""
    if session_store.delete_session(session_id):
        return {"message": "Session deleted"}
    return {"message": "Session not found"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}
