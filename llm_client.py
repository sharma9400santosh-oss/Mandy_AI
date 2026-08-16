"""
Optional real conversational-AI backend for Mandy.

Off by default. To enable: put your Anthropic API key in Settings (or
in an environment variable ANTHROPIC_API_KEY), and Mandy will use this
for anything that isn't a direct command -- so open-ended talk actually
gets a reasoned, context-aware reply instead of a canned line.

Note: this needs internet access on the phone. If you're offline, Mandy
automatically falls back to her built-in local responses.
"""

import json
import urllib.request
import urllib.error

SYSTEM_PROMPT = (
    "You are Mandy, a warm, emotionally intelligent personal AI assistant "
    "for a car navigation app. You speak concisely (1-3 sentences, this is "
    "read aloud while driving). Match the user's emotional tone with care "
    "-- calm and supportive if they sound stressed, upbeat if they sound "
    "happy, brisk and efficient if they sound rushed. Never invent facts "
    "about the vehicle, calls, or navigation status. If asked to do something "
    "actionable (navigate, call, play music), say you'll need that as a "
    "direct command rather than pretending to do it."
)


class ClaudeMandyClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/messages"
        self._history = []  # list of {"role": ..., "content": ...}

    def reply(self, text: str, emotion: str, user_name: str = "there") -> str:
        if not self.api_key:
            return "I don't have a conversational AI connected yet -- add an API key in Settings."

        self._history.append({"role": "user", "content": text})

        body = {
            "model": self.model,
            "max_tokens": 300,
            "system": SYSTEM_PROMPT,
            "messages": self._history[-10:],  # keep recent context only
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply_text = "".join(
                    block.get("text", "")
                    for block in data.get("content", [])
                    if block.get("type") == "text"
                )
                self._history.append({"role": "assistant", "content": reply_text})
                return reply_text or "I'm here, just not sure what to say to that."
        except urllib.error.URLError:
            return "I couldn't reach the AI service -- might be offline. Here locally with you though."
        except Exception as exc:  # noqa: BLE001
            return f"Something went wrong reaching the AI backend ({exc})."
