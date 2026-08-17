"""
server.py  -- PHASE 3 DYNAMIC GROQ BACKEND
------------------------------------------
A stateful backend server that connects the voice agent interface to the Groq
API. System tools are exposed directly to the model for automatic tool execution.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import RateLimitError

from groq_tools import ChatSession

app = FastAPI(title="VibeAgent Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start a stateful chat session with automatic local tool execution
chat_session = ChatSession()

class Command(BaseModel):
    text: str

@app.post("/command")
def handle_command(cmd: Command):
    try:
        # Send message to the model; it will execute any needed tools and return the final text
        response = chat_session.send_message(cmd.text)
        return {"result": response, "action": "groq_chat"}
    except RateLimitError as e:
        return {"result": f"I'm out of breath for the day — my free API token budget is used up. Try again in a little while (check Groq console for the exact reset time).", "action": "error"}
    except Exception as e:
        return {"result": f"Sorry, my brain encountered an error: {e}", "action": "error"}

from actions import get_weather

@app.get("/weather")
def get_current_weather(city: str = "Gombe"):
    return {"weather": get_weather(city)}

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve the frontend build
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")