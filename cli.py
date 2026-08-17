"""
cli.py  -- PHASE 5 DYNAMIC GROQ CLI
-----------------------------------
Desktop CLI loop that communicates with the Groq API to execute system tasks
and chat with the user via terminal input/output.
"""

import pyttsx3

from groq_tools import ChatSession

engine = pyttsx3.init()

def speak(text: str):
    print(f"Agent: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

chat_session = ChatSession()

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

            # Send message to the model; tools run automatically behind the scenes
            response = chat_session.send_message(text)
            speak(response)
        except (KeyboardInterrupt, EOFError):
            speak("Goodbye.")
            break
        except Exception as e:
            speak(f"Oops, I had a brain glitch: {e}")