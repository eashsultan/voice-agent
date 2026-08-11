# Rule-Based Voice Agent — Full Stack, No External Model

Zero ML, zero downloaded weights, zero cloud API calls. Every "decision"
is pattern matching you write and can read top to bottom.

## Structure
```
backend/
  rules.py     Phase 1 - pattern matching -> action decisions
  actions.py   Phase 2 - functions that actually do things
  server.py    Phase 3 - FastAPI backend, exposes /command endpoint
  cli.py       Phase 5 - desktop CLI loop with offline TTS
frontend/
  index.html   Phase 4 - web UI, browser mic + browser TTS
```

## Phase 1: Rule engine
Just Python + regex. Test it standalone:
```python
from rules import parse_command
print(parse_command("open vs code"))
# {'action': 'open_app', 'args': {'app_name': 'vscode'}}
```

## Phase 2: Actions
The real functions (open apps, write files, generate a template website).
Test standalone:
```python
from actions import TOOLS
TOOLS["get_time"]()
```

## Phase 3: Backend server
```
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```
Test it:
```
curl -X POST http://localhost:8000/command -H "Content-Type: application/json" -d "{\"text\": \"what time is it\"}"
```

## Phase 4: Frontend
With the server running, open `http://localhost:8000` in Chrome.
- Type a command and hit Send, or
- Click 🎤 and speak — this uses Chrome's built-in `webkitSpeechRecognition`,
  which is NOT a model you install; it ships in the browser.
- Responses are read aloud via the browser's built-in `speechSynthesis`.

This is the "full app" experience: web page, mic input, spoken output,
real actions on your machine.

## Phase 5: Desktop CLI (no browser needed)
```
cd backend
pip install pyttsx3
python cli.py
```
Type commands, agent speaks back via your OS's native voice engine
(fully offline). True offline speech *input* without any ML model isn't
realistic — type here, or use the Phase 4 browser mic instead.

## Extending
Add a capability in 2 steps:
1. Add a pattern branch in `rules.py` returning `{"action": "your_action", "args": {...}}`
2. Add the matching function in `actions.py` and register it in `TOOLS`

## What this can and can't do (be realistic)
- CAN: reliably run any command you explicitly wrote a rule for
- CAN'T: understand phrasing you didn't anticipate, generate novel code,
  or "reason" about ambiguous requests — that's what the LLM version
  (Gemma 4 via Ollama) is for, if you ever want to combine the two:
  rules first for known commands, fall back to a local model for
  anything unmatched.
