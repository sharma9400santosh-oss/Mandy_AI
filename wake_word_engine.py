"""
Wake-word engine: continuously listens (in short bursts) for a wake
phrase like "Hi Mandy" or "Hey Mandy", then hands off to the normal
command flow -- but only if the voice matches the enrolled voiceprint
(if one exists).

HONEST NOTE ON BATTERY/DATA: unlike a dedicated wake-word chip (used in
smart speakers), this re-runs full speech recognition in a loop, which
uses more battery and (on non-offline recognition) more data than a
true low-power wake word. Fine for a car where the phone is usually
plugged in and connected; less ideal for all-day pocket use.
"""

import re
import threading
import time

import settings_store as store
import voiceprint_engine as voiceprint
from voice_engine import VoiceEngine

DEFAULT_WAKE_PATTERNS = [
    r"\bhi,?\s*mandy\b",
    r"\bhey,?\s*mandy\b",
    r"\bmandy\b",  # broad fallback: her name alone also wakes her
]


class WakeWordEngine:
    def __init__(self, on_wake_detected, on_state_change=None, on_rejected_voice=None):
        """
        on_wake_detected(remaining_text: str): called when a wake phrase
            is heard AND the voice matches (or no profile is enrolled).
            remaining_text is whatever followed the wake phrase in the
            same utterance (may be empty, meaning "listen for the
            command separately").
        on_state_change(state: str): "idle_listening" / "wake_heard" /
            "voice_rejected"
        on_rejected_voice(similarity: float): called when a wake phrase
            was heard but the voice didn't match the enrolled profile.
        """
        self.on_wake_detected = on_wake_detected
        self.on_state_change = on_state_change
        self.on_rejected_voice = on_rejected_voice

        self._running = False
        self._thread = None
        self._voice_engine = VoiceEngine(
            on_result=self._handle_result,
            on_error=self._handle_error,
        )

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            if self.on_state_change:
                self.on_state_change("idle_listening")
            self._voice_engine.listen_once()
            time.sleep(0.4)  # brief pause between listening bursts

    def _wake_patterns(self):
        patterns = list(DEFAULT_WAKE_PATTERNS)
        custom_phrase = store.get("wake_phrase")
        if custom_phrase:
            escaped = re.escape(custom_phrase.lower().rstrip("."))
            patterns.insert(0, escaped)
        return patterns

    def _handle_result(self, text, raw_audio):
        if not self._running:
            return

        lowered = text.lower().strip()
        matched_pattern = None
        for pattern in self._wake_patterns():
            match = re.search(pattern, lowered)
            if match:
                matched_pattern = match
                break

        if not matched_pattern:
            return  # not the wake phrase, keep listening silently

        is_match, similarity, reason = voiceprint.verify(raw_audio)

        if not is_match:
            if self.on_state_change:
                self.on_state_change("voice_rejected")
            if self.on_rejected_voice:
                self.on_rejected_voice(similarity)
            return

        if self.on_state_change:
            self.on_state_change("wake_heard")

        remaining = lowered[matched_pattern.end():].strip(" ,.")
        self.on_wake_detected(remaining)

    def _handle_error(self, message):
        pass  # silent timeouts/no-speech are expected constantly in this loop
