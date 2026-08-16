"""
Mandy's "brain": takes what you said, figures out what you want, and
produces a (response_text, emotion, action) tuple.

Two layers:
  1. Fast local intent matching for direct commands (navigate, call,
     play music, open settings, etc) -- instant, no internet needed.
  2. Fallback to a real conversational AI (optional) for anything that
     isn't a recognized command -- e.g. "Mandy, I'm exhausted today" ->
     a genuinely generated, context-aware, empathetic reply, instead of
     a canned line.

The LLM fallback is OFF by default (no API key configured). Local
intents work immediately with zero setup.
"""

import re
import json

from navigation import extract_destination


ACTIONS = {
    "navigate": "navigate",
    "call": "call",
    "play_music": "play_music",
    "youtube": "youtube",
    "radio": "radio",
    "open_settings": "open_settings",
    "open_dashboard": "open_dashboard",
    "none": "none",
}


# --- crude sentiment/emotion detection from word choice (offline, fast) ---
STRESS_WORDS = ["exhausted", "tired", "stressed", "angry", "frustrated",
                "annoyed", "worried", "anxious", "pissed", "hate"]
URGENT_WORDS = ["now", "immediately", "hurry", "quick", "asap", "emergency"]
HAPPY_WORDS = ["great", "awesome", "happy", "excited", "love", "amazing"]


def detect_emotion(text: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in STRESS_WORDS):
        return "concerned"
    if any(w in lowered for w in URGENT_WORDS):
        return "urgent"
    if any(w in lowered for w in HAPPY_WORDS):
        return "happy"
    return "neutral"


def parse_command(text: str):
    """Try to match a direct command. Returns (action, payload) or (None, None)."""
    lowered = text.lower().strip()

    destination = extract_destination(lowered)
    if any(k in lowered for k in ["navigate", "directions", "take me to", "drive to"]) and destination:
        return "navigate", destination

    call_match = re.search(r"call (.+)", lowered)
    if call_match:
        return "call", call_match.group(1).strip()

    if any(p in lowered for p in ["play", "spotify", "music"]):
        song_match = re.search(r"play (.+?)( on spotify)?$", lowered)
        song = song_match.group(1) if song_match else ""
        return "play_music", song

    if "youtube" in lowered:
        yt_match = re.search(r"youtube (.+)", lowered)
        query = yt_match.group(1) if yt_match else ""
        return "youtube", query

    if "radio" in lowered:
        return "radio", lowered

    if "setting" in lowered:
        return "open_settings", None

    if any(p in lowered for p in ["dashboard", "speedometer", "rpm", "gauge"]):
        return "open_dashboard", None

    if any(p in lowered for p in ["document", "insurance status", "puc status",
                                    "registration status", "license status", "my papers"]):
        return "open_documents", None

    if any(p in lowered for p in ["file explorer", "open files", "my files"]):
        return "open_files", None

    if any(p in lowered for p in ["wifi", "wi-fi", "bluetooth status", "connectivity"]):
        return "open_connectivity", None

    return None, None


class ConversationEngine:
    def __init__(self, llm_client=None, user_name="Santosh"):
        """
        llm_client: optional object with a `.reply(text, emotion) -> str`
        method that calls a real conversational AI (see llm_client.py).
        If None, Mandy uses built-in supportive responses only.
        """
        self.llm_client = llm_client
        self.user_name = user_name

    def process(self, spoken_text: str):
        """
        Returns a dict:
          {
            "response_text": str,
            "emotion": str,
            "action": str,       # one of ACTIONS values
            "payload": str/None, # e.g. destination, contact name, song
          }
        """
        emotion = detect_emotion(spoken_text)
        action, payload = parse_command(spoken_text)

        if action:
            response_text = self._acknowledgment(action, payload, emotion)
            return {
                "response_text": response_text,
                "emotion": emotion,
                "action": action,
                "payload": payload,
            }

        # No direct command recognized -- open conversation.
        if self.llm_client:
            reply = self.llm_client.reply(spoken_text, emotion, user_name=self.user_name)
        else:
            reply = self._fallback_reply(spoken_text, emotion)

        return {
            "response_text": reply,
            "emotion": emotion,
            "action": "none",
            "payload": None,
        }

    def _acknowledgment(self, action, payload, emotion):
        name = self.user_name
        if action == "navigate":
            return f"Understood, {name}. Navigating to {payload} now."
        if action == "call":
            return f"Calling {payload} now, {name}."
        if action == "play_music":
            return f"Playing {payload} on Spotify." if payload else "Opening Spotify."
        if action == "youtube":
            return f"Opening YouTube{' for ' + payload if payload else ''}."
        if action == "radio":
            return "Opening your radio stations."
        if action == "open_settings":
            return "Opening settings."
        if action == "open_dashboard":
            return "Here's your dashboard."
        if action == "open_documents":
            return "Here are your vehicle documents."
        if action == "open_files":
            return "Opening your files."
        if action == "open_connectivity":
            return "Here's your connectivity status."
        return "On it."

    def _fallback_reply(self, text, emotion):
        # Built-in, non-LLM supportive responses -- limited but honest,
        # not pretending to understand everything.
        if emotion == "concerned":
            return (f"I hear you, {self.user_name}. Want me to clear your "
                     f"lighter tasks first, or would you rather just talk?")
        if emotion == "urgent":
            return "Got it, I'll move fast. What do you need first?"
        if emotion == "happy":
            return "Love that energy. What are we doing next?"
        return ("I'm not fully sure how to act on that yet. Connect a "
                "conversational AI backend in settings and I'll be able "
                "to actually reason about things like that.")
