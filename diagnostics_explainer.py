"""
diagnostics_explainer.py — the "what's this light on my dashboard?" flow.

Ties three things you already have, plus the new obd_dtc reader, together:

  1. obd_dtc.read_dtc_codes(socket)   — new: pulls real fault codes off the car
  2. llm_client.ClaudeMandyClient      — existing: your Claude-backed assistant
  3. mandy_avatar.MandyAvatar          — existing: already has a 'concerned'
                                          state in STATE_COLORS, just needs
                                          to be told to use it
  4. tts_engine.TTSEngine (optional)   — existing: speaks the explanation

Usage from a warning-icon tap (dashboard_screen.py or bottom_bar.py):

    from diagnostics_explainer import DiagnosticsExplainer

    self.explainer = DiagnosticsExplainer(
        llm_client=self.llm_client,      # your existing ClaudeMandyClient
        avatar=self.avatar,              # your existing MandyAvatar, optional
        tts=self.tts_engine,             # your existing TTSEngine, optional
    )

    def on_warning_icon_pressed(self, *_):
        self.explainer.explain(self.obd_reader._socket, user_name=store.get('user_name'))

The heavy lifting (network call, DTC parsing) runs on a background thread —
same pattern your SettingsScreen already uses for voiceprint enrollment —
so it won't freeze the dashboard.
"""

import threading
from kivy.clock import mainthread

from obd_dtc import read_dtc_codes, local_hint


class DiagnosticsExplainer:

    def __init__(self, llm_client, avatar=None, tts=None, on_result=None):
        self.llm_client = llm_client
        self.avatar = avatar
        self.tts = tts
        self.on_result = on_result  # optional callback(str) for chat-log UI

    def explain(self, socket, user_name="there"):
        threading.Thread(
            target=self._explain_worker,
            args=(socket, user_name),
            daemon=True,
        ).start()

    def _explain_worker(self, socket, user_name):
        self._set_avatar_state("thinking")
        try:
            codes = read_dtc_codes(socket)
        except Exception as exc:
            self._deliver(f"I couldn't reach the car's diagnostics port just now ({exc}).")
            return

        if not codes:
            self._deliver("No stored fault codes right now — that light may have been a transient reading. Worth checking again if it comes back.")
            return

        prompt = self._build_prompt(codes)
        reply_text = None
        try:
            reply_text = self.llm_client.reply(prompt, emotion="concerned", user_name=user_name)
        except Exception:
            reply_text = None

        if not reply_text:
            # Offline / no API key fallback: use local hints so Mandy still
            # says something useful rather than nothing.
            reply_text = self._local_fallback(codes)

        self._deliver(reply_text)

    def _build_prompt(self, codes):
        hints = []
        for code in codes:
            hint = local_hint(code)
            hints.append(f"{code}" + (f" ({hint})" if hint else ""))
        codes_text = "; ".join(hints)
        return (
            "The dashboard warning light just came on. A live diagnostic scan "
            f"found the following stored fault code(s): {codes_text}. "
            "Explain in plain language what this means for the driver right now, "
            "and suggest one clear next step (keep driving and monitor, get it "
            "checked soon, or pull over)."
        )

    def _local_fallback(self, codes):
        parts = []
        for code in codes:
            hint = local_hint(code)
            parts.append(f"{code} — {hint}" if hint else f"{code}")
        return "I found a stored code but I'm offline right now: " + "; ".join(parts)

    def _deliver(self, text):
        self._set_avatar_state("speaking")
        if self.tts:
            try:
                self.tts.speak(text)
            except Exception:
                pass
        if self.on_result:
            self._call_on_result(text)

    @mainthread
    def _set_avatar_state(self, state):
        if self.avatar is not None:
            try:
                self.avatar.state = state
            except Exception:
                pass

    @mainthread
    def _call_on_result(self, text):
        self.on_result(text)
