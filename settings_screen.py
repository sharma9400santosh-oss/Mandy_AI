from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import mainthread
import threading

import settings_store as store
import voiceprint_engine as voiceprint
import android_settings
from llm_client import ClaudeMandyClient
from voice_engine import VoiceEngine
from kivy.uix.switch import Switch
import bottom_bar

ENROLLMENT_SAMPLES_NEEDED = 3


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = BoxLayout(orientation="vertical", padding=16, spacing=10)

        back_btn = Button(text="< Back", size_hint=(1, None), height=44, font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        outer.add_widget(back_btn)

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None, padding=(0, 4))
        content.bind(minimum_height=content.setter("height"))

        def add_label(text, font_size="13sp"):
            lbl = Label(text=text, font_size=font_size, size_hint_y=None, height=30)
            content.add_widget(lbl)

        content.add_widget(Label(text="Settings", font_size="24sp",
                                  size_hint_y=None, height=40))

        add_label("Your name (Mandy will address you by this)")
        self.name_input = TextInput(text=store.get("user_name"), size_hint_y=None,
                                     height=44, multiline=False)
        content.add_widget(self.name_input)

        add_label(
            "Owner phone (optional, informational only -- NOT a login or "
            "security check, just stored on this device for your own reference)",
            font_size="12sp",
        )
        self.owner_phone_input = TextInput(text=store.get("owner_phone"), size_hint_y=None,
                                            height=44, multiline=False)
        content.add_widget(self.owner_phone_input)

        add_label("Wake phrase (in addition to \"Hi Mandy\" / \"Hey Mandy\", which always work)")
        self.wake_input = TextInput(text=store.get("wake_phrase"), size_hint_y=None,
                                     height=44, multiline=False)
        content.add_widget(self.wake_input)

        add_label("Voice personality")
        self.voice_spinner = Spinner(
            text=store.get("voice_personality"),
            values=["Warm & friendly", "Professional & clear",
                    "Soft & empathetic", "Strong & confident"],
            size_hint_y=None, height=44,
        )
        content.add_widget(self.voice_spinner)

        add_label(
            "Insurer app package name (e.g. com.acko.android) -- lets the "
            "Documents screen open it directly. Find it in your insurer app's "
            "Play Store URL.",
            font_size="12sp",
        )
        self.insurer_input = TextInput(text=store.get("insurer_app_package"),
                                        size_hint_y=None, height=44, multiline=False)
        content.add_widget(self.insurer_input)

        # ---- Vehicle / trip settings ----
        content.add_widget(Label(text="Vehicle & Trip", font_size="18sp",
                                  size_hint_y=None, height=36))

        add_label("Fuel type (affects the dashboard gauge label)")
        self.fuel_type_spinner = Spinner(
            text=store.get("fuel_type"),
            values=["Petrol", "Diesel", "CNG", "Battery"],
            size_hint_y=None, height=44,
        )
        content.add_widget(self.fuel_type_spinner)

        add_label(
            "Fuel tank capacity in litres (needed to estimate km/l -- leave "
            "blank to skip the efficiency estimate)",
            font_size="12sp",
        )
        self.tank_capacity_input = TextInput(
            text=str(store.get("fuel_tank_capacity_l") or ""), size_hint_y=None,
            height=44, multiline=False, input_filter="float",
        )
        content.add_widget(self.tank_capacity_input)

        # ---- Display settings ----
        content.add_widget(Label(text="Display", font_size="18sp",
                                  size_hint_y=None, height=36))
        time_format_row = BoxLayout(size_hint_y=None, height=44, spacing=10)
        time_format_row.add_widget(Label(text="Use 24-hour time", font_size="14sp"))
        self.time_format_switch = Switch(active=store.get("time_format_24h"))
        time_format_row.add_widget(self.time_format_switch)
        content.add_widget(time_format_row)

        # ---- System ----
        content.add_widget(Label(text="System", font_size="18sp",
                                  size_hint_y=None, height=36))
        add_label(
            "Allow this app to install other apps (e.g. for the update "
            "checker's manual install step). Android requires you to "
            "approve this yourself on the next screen -- this button just "
            "takes you there.",
            font_size="12sp",
        )
        unknown_sources_btn = Button(text="Open Install Permission Settings",
                                      size_hint_y=None, height=48,
                                      background_color=(0.4, 0.4, 0.45, 1))
        unknown_sources_btn.bind(
            on_press=lambda *_: android_settings.open_unknown_sources_settings()
        )
        content.add_widget(unknown_sources_btn)

        # ---- Bottom bar customization ----
        content.add_widget(Label(text="Bottom Bar Shortcuts", font_size="18sp",
                                  size_hint_y=None, height=36))
        add_label(
            "Tap to toggle which shortcuts show in the bottom bar on the "
            "Home screen. Selected ones are highlighted, in the order shown.",
            font_size="12sp",
        )

        self._bottom_bar_selection = bottom_bar.get_bottom_bar_config()
        self._bottom_bar_buttons = {}

        from kivy.uix.gridlayout import GridLayout
        bar_grid = GridLayout(cols=4, spacing=6, size_hint_y=None)
        bar_grid.bind(minimum_height=bar_grid.setter("height"))
        for key, (label, kind) in bottom_bar.AVAILABLE_SHORTCUTS.items():
            btn = Button(text=label, size_hint_y=None, height=44, font_size="12sp")
            btn.background_color = (
                (0.2, 0.55, 0.85, 1) if key in self._bottom_bar_selection
                else (0.25, 0.25, 0.3, 1)
            )
            btn.bind(on_press=lambda inst, k=key: self._toggle_bottom_bar_item(k))
            self._bottom_bar_buttons[key] = btn
            bar_grid.add_widget(btn)
        content.add_widget(bar_grid)

        # ---- Voice recognition / enrollment ----
        content.add_widget(Label(
            text="Voice Recognition",
            font_size="18sp", size_hint_y=None, height=36))
        add_label(
            "Train Mandy on a few samples of your voice so she only acts on "
            "commands that sound like you. This is a lightweight on-device "
            "check (pitch/energy/rhythm), not bank-grade security -- it "
            "filters out clearly different voices, not a perfect impression.",
            font_size="12sp",
        )

        self.enroll_status_label = Label(
            text=self._enrollment_status_text(),
            font_size="13sp", size_hint_y=None, height=30,
        )
        content.add_widget(self.enroll_status_label)

        enroll_row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        self.enroll_btn = Button(text="Train Mandy on my voice",
                                  background_color=(0.2, 0.55, 0.85, 1))
        self.enroll_btn.bind(on_press=self._start_enrollment)
        clear_btn = Button(text="Clear voiceprint",
                            background_color=(0.5, 0.2, 0.2, 1))
        clear_btn.bind(on_press=self._clear_voiceprint)
        enroll_row.add_widget(self.enroll_btn)
        enroll_row.add_widget(clear_btn)
        content.add_widget(enroll_row)

        # ---- AI backend ----
        add_label(
            "Conversational AI API key (optional - enables real open-ended "
            "conversation instead of built-in responses)",
            font_size="12sp",
        )
        self.api_key_input = TextInput(text=store.get("api_key"), size_hint_y=None,
                                        height=44, multiline=False, password=True)
        content.add_widget(self.api_key_input)

        # ---- Update checker ----
        content.add_widget(Label(text="App Updates", font_size="18sp",
                                  size_hint_y=None, height=36))
        add_label(
            "GitHub repo (e.g. yourname/Mandy) to check for new releases. "
            "This only checks and opens the release page -- it never "
            "downloads or installs anything automatically. You still tap "
            "to install, same as any Android app.",
            font_size="12sp",
        )
        self.repo_input = TextInput(text=store.get("update_check_repo"), size_hint_y=None,
                                     height=44, multiline=False,
                                     hint_text="yourusername/Mandy")
        content.add_widget(self.repo_input)

        update_row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        check_update_btn = Button(text="Check for updates",
                                   background_color=(0.2, 0.55, 0.85, 1))
        check_update_btn.bind(on_press=self._check_for_updates)
        self.open_release_btn = Button(text="Open release page", disabled=True,
                                        background_color=(0.3, 0.5, 0.3, 1))
        self.open_release_btn.bind(on_press=self._open_release_page)
        update_row.add_widget(check_update_btn)
        update_row.add_widget(self.open_release_btn)
        content.add_widget(update_row)

        self.update_status_label = Label(text="", font_size="13sp",
                                          size_hint_y=None, height=30)
        content.add_widget(self.update_status_label)
        self._latest_release_url = None

        save_btn = Button(text="Save Settings", font_size="18sp", size_hint_y=None,
                           height=50, background_color=(0.2, 0.6, 0.3, 1))
        save_btn.bind(on_press=self._save)
        content.add_widget(save_btn)

        advanced_btn = Button(text="Advanced mode", font_size="14sp", size_hint_y=None,
                               height=40, background_color=(0.3, 0.3, 0.34, 1))
        advanced_btn.bind(
            on_press=lambda *_: setattr(self.manager, "current", "advanced")
        )
        content.add_widget(advanced_btn)

        self.status_label = Label(text="", font_size="13sp", size_hint_y=None, height=30)
        content.add_widget(self.status_label)

        scroll.add_widget(content)
        outer.add_widget(scroll)
        self.add_widget(outer)

        self._enroll_engine = None
        self._enroll_samples = []

    def _enrollment_status_text(self):
        return ("Voiceprint: trained" if voiceprint.has_enrolled_profile()
                else "Voiceprint: not trained yet")

    # ---------------- Enrollment flow ----------------

    def _start_enrollment(self, *_):
        self._enroll_samples = []
        self.enroll_btn.disabled = True
        self._enroll_engine = VoiceEngine(
            on_result=self._on_enroll_sample,
            on_error=self._on_enroll_error,
        )
        self._prompt_next_sample()

    def _prompt_next_sample(self):
        sample_num = len(self._enroll_samples) + 1
        self.enroll_status_label.text = (
            f"Say a natural sentence out loud ({sample_num}/{ENROLLMENT_SAMPLES_NEEDED})..."
        )
        threading.Thread(target=self._enroll_engine.listen_once, daemon=True).start()

    @mainthread
    def _on_enroll_sample(self, text, raw_audio):
        features = voiceprint.extract_features(raw_audio)
        if features is None:
            self.enroll_status_label.text = "Couldn't analyze that -- try again, a bit louder."
            threading.Thread(target=self._enroll_engine.listen_once, daemon=True).start()
            return

        self._enroll_samples.append(features)

        if len(self._enroll_samples) >= ENROLLMENT_SAMPLES_NEEDED:
            success = voiceprint.enroll(self._enroll_samples)
            self.enroll_btn.disabled = False
            self.enroll_status_label.text = (
                self._enrollment_status_text() if success
                else "Enrollment failed -- please try again."
            )
        else:
            self._prompt_next_sample()

    @mainthread
    def _on_enroll_error(self, message):
        self.enroll_status_label.text = f"Didn't catch that ({message}). Try again."
        threading.Thread(target=self._enroll_engine.listen_once, daemon=True).start()

    def _clear_voiceprint(self, *_):
        voiceprint.clear_profile()
        self.enroll_status_label.text = self._enrollment_status_text()

    # ---------------- Update checking ----------------

    def _check_for_updates(self, *_):
        repo = self.repo_input.text.strip()
        store.set("update_check_repo", repo)
        self.update_status_label.text = "Checking..."
        self.open_release_btn.disabled = True
        threading.Thread(target=self._run_update_check, args=(repo,), daemon=True).start()

    def _run_update_check(self, repo):
        import update_checker

        version, url, error = update_checker.check_latest_release(repo)
        self._on_update_check_result(version, url, error)

    @mainthread
    def _on_update_check_result(self, version, url, error):
        if error:
            self.update_status_label.text = error
            return
        self.update_status_label.text = f"Latest release: {version}"
        self._latest_release_url = url
        self.open_release_btn.disabled = False

    def _open_release_page(self, *_):
        if self._latest_release_url:
            import update_checker
            update_checker.open_release_page(self._latest_release_url)

    # ---------------- General settings save ----------------

    def _toggle_bottom_bar_item(self, key):
        if key in self._bottom_bar_selection:
            self._bottom_bar_selection.remove(key)
            self._bottom_bar_buttons[key].background_color = (0.25, 0.25, 0.3, 1)
        else:
            self._bottom_bar_selection.append(key)
            self._bottom_bar_buttons[key].background_color = (0.2, 0.55, 0.85, 1)
        bottom_bar.set_bottom_bar_config(self._bottom_bar_selection)

        # Live-refresh the bar on Home immediately, no need to leave Settings.
        home_screen = self.manager.get_screen("home")
        home_screen.bottom_bar.refresh()

    def _save(self, *_):
        store.set("user_name", self.name_input.text.strip() or "there")
        store.set("owner_phone", self.owner_phone_input.text.strip())
        store.set("wake_phrase", self.wake_input.text.strip())
        store.set("voice_personality", self.voice_spinner.text)
        store.set("api_key", self.api_key_input.text.strip())
        store.set("insurer_app_package", self.insurer_input.text.strip())
        store.set("fuel_type", self.fuel_type_spinner.text)
        tank_text = self.tank_capacity_input.text.strip()
        store.set("fuel_tank_capacity_l", tank_text if tank_text else "")
        store.set("time_format_24h", self.time_format_switch.active)
        store.set("update_check_repo", self.repo_input.text.strip())

        home_screen = self.manager.get_screen("home")
        api_key = self.api_key_input.text.strip()
        home_screen.conversation.user_name = self.name_input.text.strip() or "there"
        if api_key:
            home_screen.conversation.llm_client = ClaudeMandyClient(api_key)
        else:
            home_screen.conversation.llm_client = None

        self.status_label.text = "Saved."
