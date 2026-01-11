from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from mistralai import Mistral

# Import tools
from tools import TOOLS, execute_tool

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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
    # Check if Mistral client is initialized
    if not mistral_client:
        raise HTTPException(
            status_code=503,
            detail="Mistral API is not configured. Please set MISTRAL_API_KEY."
        )

    # Initialize session if it doesn't exist
    if message.session_id not in sessions:
        sessions[message.session_id] = []

    # Prepare user message content
    user_content = message.content

    # If user location is provided, append it to the system context
    if message.user_location:
        user_content = f"{message.content}\n\n[User's current location: Latitude {message.user_location.latitude}, Longitude {message.user_location.longitude}]"

    # Add user message to session
    user_message = {
        "role": "user",
        "content": user_content,
        "timestamp": datetime.now().isoformat()
    }
    sessions[message.session_id].append(user_message)

    try:
        # Prepare messages for Mistral API (without timestamp)
        mistral_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in sessions[message.session_id]
        ]

        # Call Mistral API with tools
        response = mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=mistral_messages,
            tools=TOOLS,
        )

        # Handle tool calls if needed
        assistant_message_obj = response.choices[0].message

        # Check if model wants to call tools
        if assistant_message_obj.tool_calls:
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

                # Execute the tool
                tool_result = execute_tool(tool_call.function.name, arguments)

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
