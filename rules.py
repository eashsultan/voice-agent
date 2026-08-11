"""
rules.py  -- PHASE 1 DYNAMIC EXTENSION
--------------------------------------
An expanded stateful parsing engine that includes Wikipedia search, live weather,
calculations, media controls, and conversational replies.
"""

import re
import random

def parse_command(text: str, state: dict = None) -> dict:
    if state is None:
        state = {}

    t = text.lower().strip()
    user_name = state.get("variables", {}).get("name", "my friend")

    # Helper: checks if any keywords appear in the input
    def matches_any(keywords, text_segment):
        return any(k in text_segment for k in keywords)

    # --- 1. Conversational Chitchat (Friendly & Personality) ---
    if t in ("hello", "hi", "hey", "yo", "greetings", "good morning", "good afternoon", "good evening"):
        greetings = [
            f"Hello {user_name}! How are you doing today?",
            f"Hi there {user_name}! What can I do for you today?",
            f"Hey {user_name}! Ready to control your PC or just chat?"
        ]
        return {"action": "respond", "args": {"text": random.choice(greetings)}}

    if matches_any(["how are you", "how's it going", "how are you doing", "what's up", "sup"], t):
        responses = [
            f"I'm doing great, {user_name}! Just waiting to help you control your PC.",
            "I'm running smoothly! No local weights or heavy APIs slowing me down.",
            "Never better! How are things on your side?"
        ]
        return {"action": "respond", "args": {"text": random.choice(responses)}}

    if matches_any(["are you my friend", "be my friend", "my friend", "chat like a friend"], t):
        return {
            "action": "respond",
            "args": {
                "text": f"Of course I am your friend! I'm here to chat, listen, and help you manage your computer whenever you need."
            }
        }

    if t in ("who are you", "what are you", "what is your name", "tell me about yourself"):
        return {
            "action": "respond",
            "args": {
                "text": f"I'm VibeAgent, your lightweight Python voice assistant! I can run terminal commands, control your mouse, change your volume, and keep you company."
            }
        }

    if matches_any(["who made you", "who created you", "who is your developer"], t):
        return {
            "action": "respond",
            "args": {"text": "I was created as a lightweight assistant by you and Antigravity. I run entirely on your local machine!"}
        }

    if t in ("thank you", "thanks", "appreciate it", "great job", "good job"):
        thanks_replies = [
            "You're very welcome!",
            f"Anytime, {user_name}!",
            "Glad I could help!"
        ]
        return {"action": "respond", "args": {"text": random.choice(thanks_replies)}}

    if matches_any(["tell me a joke", "make me laugh", "joke"], t):
        jokes = [
            "Why do programmers wear glasses? Because they can't C#!",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "There are 10 types of people in the world: those who understand binary, and those who don't.",
            "What is a programmer's favorite hangout place? Foo Bar!"
        ]
        return {"action": "respond", "args": {"text": random.choice(jokes)}}

    if matches_any(["hobbies", "your hobby", "what do you do for fun"], t):
        return {
            "action": "respond",
            "args": {"text": "My favorite hobby is reading system logs, calculating math problems, and listening to your voice!"}
        }

    if matches_any(["secret", "tell me a secret"], t):
        return {
            "action": "respond",
            "args": {"text": "My secret is that I secretly enjoy it when you give me terminal commands to execute!"}
        }

    if matches_any(["meaning of life"], t):
        return {
            "action": "respond",
            "args": {"text": "The meaning of life is 42. Or perhaps, it is enjoying this chat with you!"}
        }

    # --- 2. Quote Generator ---
    if matches_any(["quote", "motivation", "inspire me"], t):
        return {"action": "get_quote", "args": {}}

    # --- 3. Live Weather Info ---
    # Matches "weather in london", "weather", "what's the weather like"
    weather_match = re.search(r"weather(?:\s+in\s+([a-zA-Z\s]+))?", t)
    if weather_match:
        city = weather_match.group(1) or ""
        return {"action": "get_weather", "args": {"city": city.strip()}}

    # --- 4. Web Searches (Google & YouTube) ---
    g_search = re.match(r"(?:search google for|google|search for)\s+(.+)", t)
    if g_search:
        return {"action": "search_google", "args": {"query": g_search.group(1)}}

    yt_search = re.match(r"(?:search youtube for|play on youtube|youtube)\s+(.+)", t)
    if yt_search:
        return {"action": "search_youtube", "args": {"query": yt_search.group(1)}}

    # --- 5. Wikipedia / DDG Instant Answer lookup ---
    info_match = re.match(r"(?:what is|what's|define|tell me about)\s+(?!my\s+)(.+)", t)
    if info_match:
        # Ignore common state/time prompts to prevent collision
        query = info_match.group(1).strip()
        if query not in ("the time", "time", "weather", "your name", "your hobby"):
            return {"action": "wiki_search", "args": {"query": query}}

    # --- 6. Quick Calculator ---
    calc_match = re.match(r"(?:calculate|what is|compute)\s+([\d\s\+\-\*\/\(\)\.]+)", t)
    if calc_match:
        # Only evaluate if it contains numbers and operator characters
        expr = calc_match.group(1).strip()
        if re.search(r'\d', expr):
            return {"action": "calculate", "args": {"expression": expr}}

    # --- 7. Memory / Variables: "remember my email is test@test.com" ---
    rem_match = re.match(r"(?:remember|save)\s+(?:my\s+)?(\S+)\s+(?:is|as)\s+(.*)", t)
    if rem_match:
        return {
            "action": "store_variable",
            "args": {"key": rem_match.group(1), "value": rem_match.group(2)}
        }

    # --- 8. Retrieve Memory: "what is my email" / "who am i" ---
    if t in ("who am i", "what's my name", "what is my name"):
        return {"action": "get_variable", "args": {"key": "name"}}
    
    get_match = re.match(r"what is my\s+(\S+)", t)
    if get_match:
        return {"action": "get_variable", "args": {"key": get_match.group(1)}}

    # --- 9. Media & Volume Controls ---
    if t in ("play", "pause", "play music", "pause music"):
        return {"action": "gui_press", "args": {"key": "playpause"}}
    if t in ("next track", "next song", "skip song"):
        return {"action": "gui_press", "args": {"key": "nexttrack"}}
    if t in ("previous track", "previous song", "go back song"):
        return {"action": "gui_press", "args": {"key": "prevtrack"}}

    if "volume" in t:
        if "up" in t or "raise" in t or "louder" in t:
            return {"action": "system_volume", "args": {"direction": "up"}}
        elif "down" in t or "lower" in t or "quieter" in t:
            return {"action": "system_volume", "args": {"direction": "down"}}
        elif "mute" in t:
            return {"action": "system_volume", "args": {"direction": "mute"}}
        elif "unmute" in t:
            return {"action": "system_volume", "args": {"direction": "unmute"}}

    # --- 10. System Info & Power ---
    if matches_any(["system info", "sysinfo", "specs", "cpu info", "os info"], t):
        return {"action": "system_info", "args": {}}

    if t in ("lock screen", "lock pc", "lock computer"):
        return {"action": "system_power", "args": {"action": "lock"}}
    if t in ("sleep mode", "suspend pc", "put computer to sleep"):
        return {"action": "system_power", "args": {"action": "sleep"}}

    # --- 11. Context App Control: "close it" ---
    if t in ("close it", "stop it", "terminate it", "exit it"):
        last_app = state.get("last_app")
        if last_app:
            return {"action": "close_app", "args": {"app_name": last_app}}
        else:
            return {"action": "respond", "args": {"text": "I don't remember what app was open last."}}

    # --- 12. App Launching ---
    if matches_any(["open", "launch", "start", "run app"], t):
        if "vs code" in t or "vscode" in t:
            return {"action": "open_app", "args": {"app_name": "vscode"}}
        elif "browser" in t:
            return {"action": "open_app", "args": {"app_name": "browser"}}
        elif "chrome" in t:
            return {"action": "open_app", "args": {"app_name": "chrome"}}
        elif "terminal" in t or "shell" in t:
            return {"action": "open_app", "args": {"app_name": "terminal"}}

    # --- 13. Web URLs ---
    url_match = re.search(r"(?:open|go to|visit)\s+([a-zA-Z0-9\-]+\.[a-zA-Z]{2,})", t)
    if url_match:
        return {"action": "open_url", "args": {"url": url_match.group(1)}}

    # --- 14. GUI Mouse/Keyboard Control ---
    click_match = re.match(r"click\s+(?:at\s+)?(\d+)\s*,?\s*(\d+)", t)
    if click_match:
        return {"action": "gui_click", "args": {"x": int(click_match.group(1)), "y": int(click_match.group(2))}}
    
    if t == "click" or t == "left click":
        return {"action": "gui_click", "args": {}}
    if t == "right click":
        return {"action": "gui_click", "args": {"button": "right"}}

    type_match = re.match(r"type\s+(.*)", t)
    if type_match:
        return {"action": "gui_type", "args": {"text": type_match.group(1)}}

    press_match = re.match(r"press\s+(\S+)", t)
    if press_match:
        return {"action": "gui_press", "args": {"key": press_match.group(1)}}

    if matches_any(["screenshot", "take a screen shot", "snap screen"], t):
        return {"action": "gui_screenshot", "args": {}}

    # --- 15. File operations & Page Generation ---
    file_match = re.match(r"write file (\S+)\s+(.*)", t)
    if file_match:
        return {
            "action": "write_file",
            "args": {"path": file_match.group(1), "content": file_match.group(2)},
        }

    site_match = re.match(r"(?:generate|create|make) (?:a )?website (?:about|for) (.+)", t)
    if site_match:
        return {"action": "generate_website", "args": {"topic": site_match.group(1)}}

    # --- 16. Simple system queries ---
    if t in ("what time is it", "what's the time"):
        return {"action": "get_time", "args": {}}

    if t in ("quit", "exit", "stop", "shut down"):
        return {"action": "shutdown", "args": {}}

    # --- 17. Arbitrary Shell Execution ---
    shell_match = re.match(r"(?:run command|run|execute|shell)\s+(.+)", t)
    if shell_match:
        return {"action": "run_terminal_command", "args": {"command": shell_match.group(1)}}

    # --- Fallback ---
    return {
        "action": "respond",
        "args": {
            "text": f"I didn't quite catch that. Try asking for weather, a joke, search Google, or calculate a math equation."
        },
    }
