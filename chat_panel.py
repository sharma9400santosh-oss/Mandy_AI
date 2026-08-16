"""
chat_panel.py — the on-screen, always-visible chat log from the browser
prototype, wired to your *real* ConversationEngine instead of a mock.

Decompiling conversation_engine.pyc recovered its actual public method:

    class ConversationEngine:
        def __init__(self, llm_client, user_name='Santosh'): ...
        def process(self, spoken_text) -> {
            'action': one of ACTIONS ('navigate','call','play_music','youtube',
                       'radio','open_settings','open_dashboard','open_connectivity',
                       'open_documents','open_files','none'),
            'payload': str | None,      # e.g. destination for 'navigate'
            'response_text': str,       # what Mandy says back
            'emotion': 'happy'|'urgent'|'concerned'|'neutral',
        }

So far in v10 this only seems to be driven by voice (wake word -> VoiceEngine
-> ConversationEngine -> TTSEngine). This widget adds a typed/visible
equivalent: a scrollable message log plus a text box, matching the browser
prototype's chat panel, so Mandy's responses are readable (useful with
the radio on, or for anyone who can't rely on audio alone) and so
diagnostics explanations (see diagnostics_explainer.py) have somewhere to
land as text, not just speech.

Usage (home_screen.py or dashboard_screen.py):

    from chat_panel import ChatPanel

    self.chat_panel = ChatPanel(
        conversation_engine=self.conversation_engine,  # your existing instance
        avatar=self.avatar,
        tts=self.tts_engine,
        screen_manager=self.manager,
    )
    self.add_widget(self.chat_panel)

    # diagnostics_explainer.py's on_result can point straight at it:
    self.explainer = DiagnosticsExplainer(..., on_result=self.chat_panel.add_mandy_message)
"""

import threading
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.clock import mainthread

# Screens that 'open_*' actions map straight onto (matches main.py's
# ScreenManager screen names exactly).
_OPEN_ACTION_SCREENS = {
    "open_settings": "settings",
    "open_dashboard": "dashboard",
    "open_connectivity": "connectivity",
    "open_documents": "documents",
    "open_files": "files",
}


class _MessageBubble(Label):
    def __init__(self, text, is_user, **kwargs):
        super().__init__(
            text=text,
            size_hint_y=None,
            halign="right" if is_user else "left",
            valign="middle",
            padding=(dp(10), dp(8)),
            **kwargs
        )
        self.bind(width=self._update_text_size)
        self.bind(texture_size=self._update_height)
        self.color = (0.3, 0.85, 0.75, 1) if is_user else (0.93, 0.93, 0.94, 1)

    def _update_text_size(self, *_):
        self.text_size = (self.width * 0.9, None)

    def _update_height(self, *_):
        self.height = self.texture_size[1] + dp(16)


class ChatPanel(BoxLayout):

    def __init__(self, conversation_engine, avatar=None, tts=None,
                 screen_manager=None, action_handlers=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        super().__init__(**kwargs)
        self.conversation_engine = conversation_engine
        self.avatar = avatar
        self.tts = tts
        self.screen_manager = screen_manager
        # Optional override map: {'navigate': fn(payload), 'call': fn(payload), ...}
        self.action_handlers = action_handlers or {}

        self._scroll = ScrollView(size_hint=(1, 1))
        self._log = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=dp(6))
        self._log.bind(minimum_height=self._log.setter("height"))
        self._scroll.add_widget(self._log)
        self.add_widget(self._scroll)

        input_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(6))
        self._input = TextInput(multiline=False, hint_text="Ask Mandy anything...")
        self._input.bind(on_text_validate=lambda *_: self._send())
        send_btn = Button(text="Send", size_hint_x=None, width=dp(80), on_release=lambda *_: self._send())
        input_row.add_widget(self._input)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)

        self.add_mandy_message("Hi, I'm Mandy. Ask me anything, or tap a warning light to run a live diagnostic.")

    # ---------- public API ----------

    def add_user_message(self, text):
        self._append(text, is_user=True)

    @mainthread
    def add_mandy_message(self, text):
        self._append(text, is_user=False)

    # ---------- internals ----------

    def _append(self, text, is_user):
        bubble = _MessageBubble(text, is_user)
        self._log.add_widget(bubble)
        self._scroll.scroll_y = 0  # snap to newest message (log grows downward)

    def _send(self):
        text = self._input.text.strip()
        if not text:
            return
        self._input.text = ""
        self.add_user_message(text)
        self._set_avatar_state("thinking")
        threading.Thread(target=self._process_worker, args=(text,), daemon=True).start()

    def _process_worker(self, text):
        try:
            result = self.conversation_engine.process(text)
        except Exception as exc:
            self.add_mandy_message(f"Sorry, I hit an error: {exc}")
            self._set_avatar_state("idle")
            return

        response_text = (result or {}).get("response_text") or "..."
        action = (result or {}).get("action", "none")
        payload = (result or {}).get("payload")
        emotion = (result or {}).get("emotion", "neutral")

        avatar_state = "concerned" if emotion == "concerned" else "speaking"
        self._set_avatar_state(avatar_state)
        self.add_mandy_message(response_text)

        if self.tts:
            try:
                self.tts.speak(response_text)
            except Exception:
                pass

        self._dispatch_action(action, payload)
        self._set_avatar_state_later("idle", delay=2.5)

    def _dispatch_action(self, action, payload):
        handler = self.action_handlers.get(action)
        if handler:
            try:
                handler(payload)
            except Exception:
                pass
            return

        if action in _OPEN_ACTION_SCREENS and self.screen_manager:
            self._set_screen(_OPEN_ACTION_SCREENS[action])

    @mainthread
    def _set_screen(self, name):
        self.screen_manager.current = name

    @mainthread
    def _set_avatar_state(self, state):
        if self.avatar is not None:
            try:
                self.avatar.state = state
            except Exception:
                pass

    def _set_avatar_state_later(self, state, delay=2.0):
        from kivy.clock import Clock
        Clock.schedule_once(lambda *_: self._set_avatar_state(state), delay)
