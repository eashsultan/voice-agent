"""
actions.py  -- PHASE 2 UPGRADED WITH WEB QUERIES
-----------------------------------------------
Python system, GUI automation, and lightweight web query engines.
Safe imports and no external libraries (except standard libraries + optional pyautogui)
are used to keep the project completely offline/model-free.
"""

import subprocess
import platform
import webbrowser
import os
import datetime
import urllib.request
import urllib.parse
import json
import random
import re

# Safely mock mouseinfo to prevent tkinter dependencies on Linux
import sys
from types import ModuleType
sys.modules['mouseinfo'] = ModuleType('mouseinfo')

# Attempt to import pyautogui safely
try:
    import pyautogui
    pyautogui.PAUSE = 0.5
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False

SYSTEM = platform.system()  # 'Windows' | 'Darwin' | 'Linux'

def open_app(app_name: str):
    aliases = {
        "vscode": {"Darwin": "Visual Studio Code", "Windows": "code", "Linux": "code"},
        "browser": {"Darwin": "Safari", "Windows": "chrome", "Linux": "xdg-open"},
        "chrome": {"Darwin": "Google Chrome", "Windows": "chrome", "Linux": "google-chrome"},
        "terminal": {"Darwin": "Terminal", "Windows": "cmd", "Linux": "x-terminal-emulator"},
    }
    target = aliases.get(app_name, {}).get(SYSTEM, app_name)
    try:
        if SYSTEM == "Darwin":
            subprocess.run(["open", "-a", target], check=True)
        elif SYSTEM == "Windows":
            subprocess.run(["start", target], shell=True, check=True)
        else:
            subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Failed to open {app_name}: {e}"

def close_app(app_name: str):
    process_map = {
        "vscode": "code",
        "chrome": "chrome",
        "browser": "firefox" if SYSTEM == "Linux" else "browser",
        "terminal": "x-terminal-emulator"
    }
    proc_name = process_map.get(app_name, app_name)
    try:
        if SYSTEM == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", f"{proc_name}.exe"], check=True)
        elif SYSTEM == "Darwin":
            subprocess.run(["killall", proc_name], check=True)
        else:
            subprocess.run(["pkill", proc_name], check=True)
        return f"Closed {app_name}"
    except Exception as e:
        return f"Could not close process '{app_name}': {e}"

def open_url(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"

def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"

def generate_website(topic: str):
    html = f"""<!DOCTYPE html>
<html>
<head><title>{topic.title()}</title></head>
<body>
  <h1>Welcome to {topic.title()}</h1>
  <p>This is a starter page about {topic}. Edit this template in actions.py.</p>
</body>
</html>"""
    path = f"generated_sites/{topic.replace(' ', '_')}.html"
    return write_file(path, html)

def get_time():
    return datetime.datetime.now().strftime("It's %I:%M %p")

# --- Arbitrary Shell execution ---
def run_terminal_command(command: str):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = (result.stdout + "\n" + result.stderr).strip()
        if not output:
            return "Command executed successfully with no output."
        return output
    except Exception as e:
        return f"Command execution failed: {e}"

# --- System Volume Controls ---
def system_volume(direction: str):
    try:
        if SYSTEM == "Linux":
            if direction == "up":
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%+"], capture_output=True)
                return "Volume increased."
            elif direction == "down":
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%-"], capture_output=True)
                return "Volume decreased."
            elif direction == "mute":
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "mute"], capture_output=True)
                return "Muted audio."
            elif direction == "unmute":
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "unmute"], capture_output=True)
                return "Unmuted audio."
        elif SYSTEM == "Windows" and GUI_AVAILABLE:
            if direction == "up":
                pyautogui.press("volumeup")
                return "Volume increased"
            elif direction == "down":
                pyautogui.press("volumedown")
                return "Volume decreased"
            elif direction == "mute" or direction == "unmute":
                pyautogui.press("volumemute")
                return "Toggled mute"
        return f"Volume controls adjusted."
    except Exception as e:
        return f"Failed to adjust volume: {e}"

# --- System Information ---
def system_info():
    try:
        if SYSTEM == "Linux":
            cpu = subprocess.run("lscpu | grep 'Model name'", shell=True, capture_output=True, text=True).stdout.strip()
            mem = subprocess.run("free -h | grep Mem", shell=True, capture_output=True, text=True).stdout.strip()
            disk = subprocess.run("df -h / | tail -n 1", shell=True, capture_output=True, text=True).stdout.strip()
            return f"OS: Linux. CPU: {cpu}. Memory Usage: {mem}. Disk Status: {disk}"
        elif SYSTEM == "Windows":
            return f"OS: Windows. System Type: {platform.machine()}. Processor: {platform.processor()}"
        return f"OS: {SYSTEM}. Platform: {platform.platform()}"
    except Exception as e:
        return f"Error retrieving system information: {e}"

# --- System Power ---
def system_power(action: str):
    try:
        if SYSTEM == "Linux":
            if action == "lock":
                subprocess.Popen(["xdg-screensaver", "lock"])
                return "Locked screen."
            elif action == "sleep":
                subprocess.Popen(["systemctl", "suspend"])
                return "Putting PC to sleep."
        elif SYSTEM == "Windows":
            if action == "lock":
                subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")
                return "Locked screen."
            elif action == "sleep":
                subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return "Putting PC to sleep."
        return f"Power action '{action}' executed."
    except Exception as e:
        return f"Power action failed: {e}"

# --- GUI Controls (PyAutoGUI) ---
def gui_click(x: int = None, y: int = None, button: str = 'left'):
    if not GUI_AVAILABLE:
        return "GUI automation is not available."
    try:
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
            return f"Clicked {button} at ({x}, {y})"
        else:
            pyautogui.click(button=button)
            return f"Clicked {button}."
    except Exception as e:
        return f"GUI Click failed: {e}"

def gui_type(text: str):
    if not GUI_AVAILABLE:
        return "GUI automation is not available."
    try:
        pyautogui.write(text)
        return f"Typed: '{text}'"
    except Exception as e:
        return f"GUI Typing failed: {e}"

def gui_press(key: str):
    if not GUI_AVAILABLE:
        return "GUI automation is not available."
    try:
        if "+" in key:
            keys = key.split("+")
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        return f"Pressed {key}"
    except Exception as e:
        return f"GUI Keypress failed: {e}"

def gui_screenshot():
    if not GUI_AVAILABLE:
        return "GUI automation is not available."
    try:
        os.makedirs("frontend", exist_ok=True)
        path = "frontend/screenshot.png"
        pyautogui.screenshot(path)
        return "Screenshot saved. View it in browser at /screenshot.png."
    except Exception as e:
        return f"Screenshot failed: {e}"

# --- New Web Queries & Utilities ---

def get_quote():
    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "Believe you can and you're halfway there. - Theodore Roosevelt",
        "Simplicity is the ultimate sophistication. - Leonardo da Vinci",
        "Make it simple, but significant. - Don Draper",
        "Strive not to be a success, but rather to be of value. - Albert Einstein"
    ]
    return random.choice(quotes)

def get_weather(city: str = ""):
    try:
        # Fetch clean, text-based weather report from wttr.in
        query_city = urllib.parse.quote(city) if city else ""
        url = f"http://wttr.in/{query_city}?format=3"
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.79.1'})
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read().decode('utf-8').strip()
    except Exception as e:
        return "I couldn't fetch the weather right now. Check if you're connected to the internet."

def search_google(query: str):
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f"Searching Google for {query}"

def search_youtube(query: str):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f"Searching YouTube for {query}"

def wiki_search(query: str):
    try:
        # Use DuckDuckGo Instant Answer API (Free, public, no key)
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            abstract = data.get("AbstractText", "")
            if abstract:
                return abstract
            
            # Fallback to related topics
            related = data.get("RelatedTopics", [])
            if related and "Text" in related[0]:
                return related[0]["Text"]
            
            return f"I couldn't find a direct definition for '{query}', but you can try asking me to search Google for it!"
    except Exception as e:
        return f"Failed to retrieve information for '{query}': {e}"

def calculate(expression: str):
    try:
        # Safety check: only allow digits, arithmetic operations, parentheses and spaces
        cleaned = re.sub(r'[^0-9\+\-\*\/\(\)\.\s]', '', expression)
        # Avoid eval of empty inputs
        if not cleaned.strip():
            return "Invalid math expression."
        # Safe evaluation
        result = eval(cleaned, {"__builtins__": None}, {})
        return f"{expression.strip()} equals {result}"
    except Exception as e:
        return f"Could not calculate that: {e}"

# Expose all functions to the server
TOOLS = {
    "open_app": open_app,
    "close_app": close_app,
    "open_url": open_url,
    "write_file": write_file,
    "generate_website": generate_website,
    "get_time": get_time,
    "run_terminal_command": run_terminal_command,
    "system_volume": system_volume,
    "system_info": system_info,
    "system_power": system_power,
    "gui_click": gui_click,
    "gui_type": gui_type,
    "gui_press": gui_press,
    "gui_screenshot": gui_screenshot,
    "get_quote": get_quote,
    "get_weather": get_weather,
    "search_google": search_google,
    "search_youtube": search_youtube,
    "wiki_search": wiki_search,
    "calculate": calculate,
}
