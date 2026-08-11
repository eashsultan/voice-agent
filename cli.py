"""
cli.py  -- PHASE 5 DYNAMIC GEMINI CLI
-------------------------------------
Desktop CLI loop that communicates with the Gemini API to execute system tasks
and chat with the user via terminal input/output.
"""

import pyttsx3
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

engine = pyttsx3.init()

def speak(text: str):
    print(f"Agent: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

# --- Configure Gemini ---
import os

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split("=", 1)
                if len(parts) == 2:
                    os.environ[parts[0]] = parts[1]

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

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

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    tools=tools_list,
    system_instruction=system_instruction
)

chat_session = model.start_chat(enable_automatic_function_calling=True)

if __name__ == "__main__":
    speak("Agent ready. Type a command to chat or control your PC.")
    while True:
        try:
            text = input("\nYou: ").strip()
            if not text:
                continue
            if text.lower() in ("quit", "exit", "stop", "goodbye"):
                speak("Goodbye my friend!")
                break
            
            # Send message to Gemini; tools run automatically behind the scenes
            response = chat_session.send_message(text)
            speak(response.text)
        except (KeyboardInterrupt, EOFError):
            speak("Goodbye.")
            break
        except Exception as e:
            speak(f"Oops, I had a brain glitch: {e}")
