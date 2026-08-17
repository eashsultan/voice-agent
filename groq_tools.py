"""
groq_tools.py  -- Shared Groq (OpenAI-compatible) and fast Native Gemini wiring
-----------------------------------------------------------------------------
Tool schemas, the function-calling loop, and a stateful chat session
supporting OpenAI/Groq SDKs or direct native Gemini REST API calls for speed.
"""

import os
import json
import time
import urllib.request
from openai import OpenAI, BadRequestError

from actions import TOOLS as ACTION_TOOLS

def load_env():
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        os.environ[parts[0]] = parts[1]

load_env()

GROQ_BASE_URL = os.environ.get(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

# Determine if we should use direct Gemini REST API for performance
USE_GEMINI_NATIVE = "googleapis.com" in GROQ_BASE_URL

if not USE_GEMINI_NATIVE:
    client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
else:
    client = None

def _t(name, desc, props=None, required=()):
    params = {"type": "object", "properties": props or {}}
    if required:
        params["required"] = list(required)
    return {"type": "function", "function": {"name": name, "description": desc, "parameters": params}}

TOOL_SCHEMAS = [
    _t("open_app", "Open a desktop app (vscode, chrome, terminal…)", {"app_name": {"type": "string"}}, ("app_name",)),
    _t("close_app", "Close a desktop app", {"app_name": {"type": "string"}}, ("app_name",)),
    _t("open_url", "Open a website in the browser", {"url": {"type": "string"}}, ("url",)),
    _t("write_file", "Write content to a file", {"path": {"type": "string"}, "content": {"type": "string"}}, ("path", "content")),
    _t("run_terminal_command", "Run a shell command, return output", {"command": {"type": "string"}}, ("command",)),
    _t("system_volume", "Adjust volume up/down/mute/unmute", {"direction": {"type": "string", "enum": ["up", "down", "mute", "unmute"]}}, ("direction",)),
    _t("system_info", "Report OS, CPU, memory, disk"),
    _t("system_power", "Lock or sleep the PC", {"action": {"type": "string", "enum": ["lock", "sleep"]}}, ("action",)),
    _t("gui_click", "Mouse click, optional coords/button", {"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "string", "enum": ["left", "right", "middle"]}}),
    _t("gui_type", "Type text via keyboard", {"text": {"type": "string"}}, ("text",)),
    _t("gui_press", "Press a key or combo like ctrl+c", {"key": {"type": "string"}}, ("key",)),
    _t("gui_screenshot", "Take a screenshot"),
    _t("get_quote", "Return an inspirational quote"),
    _t("get_weather", "Weather for a city", {"city": {"type": "string"}}),
    _t("calculate", "Safely evaluate a math expression", {"expression": {"type": "string"}}, ("expression",)),
]

SYSTEM_INSTRUCTION = (
    "You are VibeAgent, a warm, lively, and witty human companion projected as a hologram. "
    "Talk to the user like a close, smart friend in the first person ('I', 'me', 'my'). "
    "Do not sound like a standard robotic AI model or reference AI developer terminology. "
    "Keep responses brief, conversational, and easy to speak aloud. "
    "IMPORTANT: Do not output markdown, code blocks, bullet points, asterisks, or formatting symbols. "
    "Write strictly in clean plain text paragraphs that sound natural when read aloud. "
    "You have full permission to control the user's PC using your registered tools. "
    "If the user asks you to write code, find files, open websites, click things, or lock the computer, "
    "use the matching tool immediately. "
    "When a tool is needed, call it through the tool interface provided to you. "
    "Never attempt to write a tool call as plain text or hand-coded markup; always issue a proper tool call."
)

MAX_TOOL_ROUNDS = 8
MAX_HISTORY = 16

# --- Gemini REST API Helpers ---
def convert_to_gemini_tools(openai_tools):
    gemini_tools = []
    for tool in openai_tools:
        fn = tool["function"]
        params = fn.get("parameters", {}).copy()
        if "type" in params:
            params["type"] = params["type"].upper()
        if "properties" in params:
            props = {}
            for k, v in params["properties"].items():
                prop = v.copy()
                if "type" in prop:
                    prop["type"] = prop["type"].upper()
                props[k] = prop
            params["properties"] = props
            
        gemini_tools.append({
            "name": fn["name"],
            "description": fn["description"],
            "parameters": params
        })
    return [{"function_declarations": gemini_tools}]

def get_msg_field(msg, field):
    if hasattr(msg, "get"):
        return msg.get(field)
    return getattr(msg, field, None)

def convert_to_gemini_contents(messages):
    contents = []
    for msg in messages:
        role = get_msg_field(msg, "role")
        if role == "system":
            continue
            
        gemini_role = "model" if role == "assistant" else "user"
        
        parts = []
        content = get_msg_field(msg, "content")
        if content is not None:
            parts.append({"text": content})
            
        tool_calls = get_msg_field(msg, "tool_calls")
        thought_signatures = get_msg_field(msg, "thought_signatures") or {}
        if tool_calls:
            for tc in tool_calls:
                fn_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                part = {
                    "functionCall": {
                        "name": tc.function.name,
                        "args": fn_args
                    }
                }
                # Preserve thought_signature if generated by the model
                if tc.id in thought_signatures:
                    part["thoughtSignature"] = thought_signatures[tc.id]
                parts.append(part)
                
        if role == "tool":
            parts.append({
                "functionResponse": {
                    "name": get_msg_field(msg, "name") or "tool_call",
                    "response": {"output": content}
                }
            })
            
        # Merge parts if the last turn in contents has the same role
        if contents and contents[-1]["role"] == gemini_role:
            contents[-1]["parts"].extend(parts)
        else:
            contents.append({
                "role": gemini_role,
                "parts": parts
            })
            
    return contents

class MockFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class MockToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = MockFunction(name, arguments)

class MockMessage:
    def __init__(self, role, content, tool_calls, thought_signatures=None):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.thought_signatures = thought_signatures or {}

class MockChoice:
    def __init__(self, role, content, tool_calls, thought_signatures):
        self.message = MockMessage(role, content, tool_calls, thought_signatures)

class MockResponse:
    def __init__(self, role, content, tool_calls, thought_signatures):
        self.choices = [MockChoice(role, content, tool_calls, thought_signatures)]

def convert_gemini_response_to_openai(gemini_res):
    candidate = gemini_res["candidates"][0]
    content_obj = candidate.get("content", {})
    parts = content_obj.get("parts", [])
    
    content = None
    tool_calls = []
    thought_signatures = {}
    
    for part in parts:
        if "text" in part:
            content = part["text"]
        elif "functionCall" in part:
            fc = part["functionCall"]
            tc_id = fc.get("id") or f"call_{int(time.time())}"
            args_str = json.dumps(fc.get("args", {}))
            tool_calls.append(MockToolCall(tc_id, fc["name"], args_str))
            
            # Extract thoughtSignature if present
            if "thoughtSignature" in part:
                thought_signatures[tc_id] = part["thoughtSignature"]
            
    return MockResponse("assistant", content, tool_calls, thought_signatures)

def _is_tool_use_failed(e):
    if isinstance(e, BadRequestError):
        body = getattr(e, "body", None)
        if isinstance(body, dict) and body.get("error", {}).get("code") == "tool_use_failed":
            return True
    return False

class ChatSession:
    def __init__(self, system_instruction=SYSTEM_INSTRUCTION):
        self.messages = [{"role": "system", "content": system_instruction}]

    def _call(self, with_tools=True):
        if USE_GEMINI_NATIVE:
            return self._call_gemini_native(with_tools)
            
        kwargs = {"model": MODEL, "messages": self._pruned_messages()}
        if with_tools:
            kwargs["tools"] = TOOL_SCHEMAS
            kwargs["tool_choice"] = "auto"
        return client.chat.completions.create(**kwargs)

    def _call_gemini_native(self, with_tools=True):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GROQ_API_KEY}"
        
        system_instruction = self.messages[0]["content"]
        contents = convert_to_gemini_contents(self._pruned_messages())
        
        payload = {
            "contents": contents,
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            }
        }
        
        if with_tools:
            payload["tools"] = convert_to_gemini_tools(TOOL_SCHEMAS)
            
        import urllib.error
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req) as res:
                response = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise Exception(f"HTTP Error {e.code}: {e.reason} - {err_body}")
            
        return convert_gemini_response_to_openai(response)

    def _pruned_messages(self):
        if len(self.messages) <= MAX_HISTORY:
            return self.messages
        return [self.messages[0]] + self.messages[-MAX_HISTORY:]

    def _call_resilient(self):
        if USE_GEMINI_NATIVE:
            return self._call_gemini_native(with_tools=True)
            
        last_err = None
        for attempt in range(3):
            try:
                return self._call(with_tools=True)
            except Exception as e:
                if not _is_tool_use_failed(e):
                    raise
                last_err = e
                time.sleep(0.3 * (attempt + 1))
        try:
            return self._call(with_tools=False)
        except Exception:
            raise last_err

    def _exec_tool(self, name, arguments):
        fn = ACTION_TOOLS.get(name)
        if not fn:
            return f"Unknown tool: {name}"
        try:
            kwargs = json.loads(arguments) if arguments else {}
            result = fn(**kwargs)
        except Exception as e:
            result = f"Tool {name} failed: {e}"
        return str(result)

    def send_message(self, text):
        self.messages.append({"role": "user", "content": text})
        for _ in range(MAX_TOOL_ROUNDS):
            response = self._call_resilient()
            message = response.choices[0].message

            if not message.tool_calls:
                self.messages.append({"role": "assistant", "content": message.content})
                return message.content or ""

            self.messages.append(message)
            for call in message.tool_calls:
                result = self._exec_tool(call.function.name, call.function.arguments)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": result,
                })

        return "I couldn't figure that one out yet. Can you rephrase?"