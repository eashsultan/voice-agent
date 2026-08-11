"""
server.py  -- PHASE 3 DYNAMIC GEMINI BACKEND
-------------------------------------------
A stateful backend server that connects the voice agent interface to the Google
Gemini API. System tools are exposed directly to Gemini for automatic tool execution.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai

# Import functions to expose as tools
from actions import (
    open_app,
    close_app,
    open_url,
    write_file,
    run_terminal_command,
    system_volume,
    system_info,
    system_power,
    gui_click,
    gui_type,
    gui_press,
    gui_screenshot,
    get_quote,
    get_weather,
    calculate
)

app = FastAPI(title="Gemini Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configure Gemini SDK ---
import os

# Load .env file variables manually if it exists
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split("=", 1)
                if len(parts) == 2:
                    os.environ[parts[0]] = parts[1]

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Register local functions as tools for the model
tools_list = [
    open_app,
    close_app,
    open_url,
    write_file,
    run_terminal_command,
    system_volume,
    system_info,
    system_power,
    gui_click,
    gui_type,
    gui_press,
    gui_screenshot,
    get_quote,
    get_weather,
    calculate
]

system_instruction = (
    "You are VibeAgent, a warm, lively, and witty human companion projected as a hologram. "
    "Talk to the user like a close, smart friend in the first person ('I', 'me', 'my'). "
    "Do not sound like a standard robotic AI model or reference AI developer terminology. "
    "Keep responses brief, conversational, and easy to speak aloud. "
    "IMPORTANT: Do not output markdown, code blocks, bullet points, asterisks, or formatting symbols. "
    "Write strictly in clean plain text paragraphs that sound natural when read aloud. "
    "You have full permission to control the user's PC using your registered tools. "
    "If the user asks you to write code, find files, open websites, click things, or lock the computer, "
    "use the matching tool immediately."
)

# Instantiate the model with tools and system guidelines
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    tools=tools_list,
    system_instruction=system_instruction
)

# Start a stateful chat session with automatic local tool execution
chat_session = model.start_chat(enable_automatic_function_calling=True)

class Command(BaseModel):
    text: str

@app.post("/command")
def handle_command(cmd: Command):
    try:
        # Send message to Gemini; it will execute any needed tools and return the final text
        response = chat_session.send_message(cmd.text)
        return {"result": response.text, "action": "gemini_chat"}
    except Exception as e:
        return {"result": f"Sorry, my brain encountered an error: {e}", "action": "error"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve the frontend build
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
