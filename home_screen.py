"""
Home screen: Mandy's face front and center, mic button, wake-word
toggle, and a quick nav bar to jump to Dashboard / Media / Calls /
Navigation / Settings.
"""

import threading

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.clock import mainthread, Clock

from mandy_avatar import MandyAvatar
from icon_grid_button import IconGridButton
from voice_engine import VoiceEngine
from tts_engine import TTSEngine
from conversation_engine import ConversationEngine
from navigation import launch_navigation
from call_manager import call_contact
from media_manager import open_spotify, open_youtube, open_radio
from wake_word_engine import WakeWordEngine
from bottom_bar import BottomBar
from llm_client import ClaudeMandyClient
import voiceprint_engine as voiceprint
import settings_store as store
import vehicle_documents as docs


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.tts = TTSEngine()

        # Load any previously-saved API key so live AI conversation works
        # immediately on app start, not just right after visiting Settings.
        saved_api_key = store.get("api_key")
        llm_client = ClaudeMandyClient(saved_api_key) if saved_api_key else None

        self.conversation = ConversationEngine(
            user_name=store.get("user_name"), llm_client=llm_client
        )
        self.voice_engine = VoiceEngine(
            on_result=self.on_speech_result,
            on_error=self.on_speech_error,
            on_listening_started=self.on_listening_started,
        )
        self.wake_engine = WakeWordEngine(
            on_wake_detected=self._on_wake_detected,
            on_state_change=self._on_wake_state_change,
            on_rejected_voice=self._on_voice_rejected,
        )

        root = BoxLayout(orientation="vertical", padding=16, spacing=10)

        nav_grid = GridLayout(cols=10, size_hint=(1, 0.16), spacing=3)
        for label, icon_name, screen_name in [
            ("Dashboard", "dashboard", "dashboard"),
            ("Media", "media", "media"),
            ("Calls", "calls", "calls"),
            ("Navigate", "navigate", "navigate"),
            ("Docs", "docs", "documents"),
            ("Files", "files", "files"),
            ("Camera", "camera", "camera"),
            ("Apps", "apps", "apps"),
            ("Connect", "connectivity", "connectivity"),
            ("Settings", "settings", "settings"),
        ]:
            icon_btn = IconGridButton(
                icon_path=f"assets/icon_{icon_name}.png",
                label_text=label,
                on_press=lambda s=screen_name: self._go_to(s),
            )
            nav_grid.add_widget(icon_btn)
        root.add_widget(nav_grid)

        self.avatar = MandyAvatar(
            face_source="assets/mandy_face.png",
            size_hint=(1, 0.48),
        )
        root.add_widget(self.avatar)

        self.status_label = Label(
            text="Tap 'Talk to Mandy', or say \"Hi Mandy\" if wake word is on",
            font_size="17sp",
            size_hint=(1, 0.09),
        )
        root.add_widget(self.status_label)

        self.heard_label = Label(
            text="",
            font_size="14sp",
            color=(0.6, 0.85, 1, 1),
            size_hint=(1, 0.08),
        )
        root.add_widget(self.heard_label)

        self.docs_banner = Label(
            text="",
            font_size="13sp",
            color=(0.95, 0.7, 0.2, 1),
            size_hint=(1, 0.06),
        )
        root.add_widget(self.docs_banner)

        wake_row = BoxLayout(size_hint=(1, 0.1), spacing=10)
        wake_row.add_widget(Label(text="Wake word (\"Hi Mandy\")", font_size="14sp"))
        self.wake_switch = Switch(active=store.get("wake_word_enabled"))
        self.wake_switch.bind(active=self._on_wake_toggle)
        wake_row.add_widget(self.wake_switch)
        root.add_widget(wake_row)

        self.mic_button = Button(
            text="Talk to Mandy",
            font_size="22sp",
            size_hint=(1, 0.15),
            background_color=(0.2, 0.5, 0.9, 1),
        )
        self.mic_button.bind(on_press=self.start_listening)
        root.add_widget(self.mic_button)

        self.bottom_bar = BottomBar(screen_manager=None, size_hint=(1, 0.09))
        root.add_widget(self.bottom_bar)

        self.add_widget(root)

        if self.wake_switch.active:
            self.wake_engine.start()

    def _go_to(self, screen_name):
        self.manager.current = screen_name

    def on_enter(self, *_):
        self._refresh_docs_banner()
        self.bottom_bar.screen_manager = self.manager
        self.bottom_bar.refresh()

    def _refresh_docs_banner(self):
        if docs.any_urgent():
            self.docs_banner.text = "⚠ One or more vehicle documents need attention -- check Docs"
        else:
            self.docs_banner.text = ""

    # ---------------- Tap-to-speak flow ----------------

    def start_listening(self, *_):
        self.status_label.text = "Listening..."
        self.mic_button.disabled = True
        self.avatar.set_state("listening")
        threading.Thread(target=self.voice_engine.listen_once, daemon=True).start()

    @mainthread
    def on_listening_started(self):
        self.status_label.text = "Listening... speak now"

    @mainthread
    def on_speech_result(self, text, raw_audio=b""):
        self.mic_button.disabled = False
        self._process_utterance(text, raw_audio)

    @mainthread
    def on_speech_error(self, message):
        self.mic_button.disabled = False
        self.avatar.set_state("idle")
        self.status_label.text = f"Didn't catch that ({message})"

    # ---------------- Wake-word flow ----------------

    def _on_wake_toggle(self, _switch, active):
        store.set("wake_word_enabled", active)
        if active:
            self.wake_engine.start()
            self.status_label.text = 'Wake word on -- say "Hi Mandy" anytime'
        else:
            self.wake_engine.stop()
            self.status_label.text = "Wake word off. Tap 'Talk to Mandy' to speak."

    @mainthread
    def _on_wake_state_change(self, state):
        if state == "wake_heard":
            self.avatar.set_state("listening")
        elif state == "voice_rejected":
            self.avatar.set_state("concerned")
            Clock.schedule_once(lambda dt: self.avatar.set_state("idle"), 1.5)
        # "idle_listening" -> no UI change, stays subtle/idle in background

    @mainthread
    def _on_voice_rejected(self, similarity):
        self.status_label.text = "Voice not recognized as yours -- ignoring."

    def _on_wake_detected(self, remaining_text):
        if remaining_text:
            # e.g. "Hey Mandy, navigate to the airport" heard in one go.
            Clock.schedule_once(
                lambda dt: self._process_utterance(remaining_text, b""), 0
            )
        else:
            # Just the wake phrase alone -- listen separately for the command.
            Clock.schedule_once(lambda dt: self._listen_for_command(), 0)

    def _listen_for_command(self):
        self.status_label.text = "Yes? I'm listening..."
        self.avatar.set_state("listening")
        threading.Thread(target=self.voice_engine.listen_once, daemon=True).start()

    # ---------------- Shared processing ----------------

    def _process_utterance(self, text, raw_audio):
        self.heard_label.text = f'You said: "{text}"'
        self.avatar.set_state("thinking")

        # Voiceprint check (applies to any command path, not just wake word,
        # so Mandy consistently only acts on commands from your voice).
        is_match, similarity, reason = voiceprint.verify(raw_audio)
        if not is_match:
            self.status_label.text = "That doesn't sound like your voice -- ignoring that request."
            self.avatar.set_state("concerned")
            Clock.schedule_once(lambda dt: self.avatar.set_state("idle"), 2)
            return

        # conversation.process() may call out to the internet (Claude API
        # for open-ended chat) -- run it off the UI thread so a slow/stalled
        # network request never freezes the app.
        threading.Thread(
            target=self._run_conversation_and_dispatch, args=(text,), daemon=True
        ).start()

    def _run_conversation_and_dispatch(self, text):
        result = self.conversation.process(text)
        self._on_conversation_result(result)

    @mainthread
    def _on_conversation_result(self, result):
        self.status_label.text = result["response_text"]
        self.avatar.set_state(
            result["emotion"] if result["emotion"] != "neutral" else "speaking"
        )

        self.tts.speak(result["response_text"], emotion=result["emotion"])
        self._execute_action(result["action"], result["payload"])

        Clock.schedule_once(lambda dt: self.avatar.set_state("idle"), 2.5)

    def _execute_action(self, action, payload):
        if action == "navigate" and payload:
            launch_navigation(payload)
        elif action == "call" and payload:
            call_contact(payload)
        elif action == "play_music":
            open_spotify(payload or "")
        elif action == "youtube":
            open_youtube(payload or "")
        elif action == "radio":
            open_radio()
        elif action == "open_settings":
            self.manager.current = "settings"
        elif action == "open_dashboard":
            self.manager.current = "dashboard"
        elif action == "open_documents":
            self.manager.current = "documents"
        elif action == "open_files":
            self.manager.current = "files"
        elif action == "open_connectivity":
            self.manager.current = "connectivity"
