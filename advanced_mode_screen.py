"""
AdvancedModeScreen — direct system-config editing (spec note 8: "Settings
should have advanced mode to make changes... to make the changes easy /
editable code").

Built on top of the existing `settings_store` (a kivy.storage.JsonStore
wrapper already used by SettingsScreen, OnboardingScreen, DashboardScreen,
etc.) — so anything editable here is automatically the same store the rest
of the app already reads from. No new persistence layer, no migration.

Wire-up (add to your project, don't replace anything):

    # main.py
    from screens.advanced_mode_screen import AdvancedModeScreen
    ...
    sm.add_widget(AdvancedModeScreen(name='advanced'))

    # screens/settings_screen.py — add a button near the other settings rows:
    Button(text='Advanced mode', on_release=lambda *_: setattr(
        self.manager, 'current', 'advanced'))
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.metrics import dp
import json

import settings_store as store

# Keys considered safe to expose in the raw editor. Deliberately excludes
# anything that should only ever be set through a dedicated, validated flow
# (api_key goes through Settings' own masked field; onboarding_complete /
# voice_profile are written by code paths that also do side effects).
EDITABLE_KEYS = [
    "wake_phrase",
    "voice_personality",
    "wake_word_enabled",
    "vehicle_number",
    "insurer_app_package",
    "speed_limit_alerts_enabled",
    "update_check_repo",
    "fuel_type",
    "fuel_tank_capacity_l",
    "vehicle_make",
    "vehicle_model",
    "climate_alert_high_c",
    "climate_alert_low_c",
    "climate_alerts_enabled",
    "bottom_bar_config",
    "time_format_24h",
]


def _coerce(raw_text, previous_value):
    """Best-effort: keep the same type the value already had."""
    if isinstance(previous_value, bool):
        return raw_text.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(previous_value, int) and not isinstance(previous_value, bool):
        try:
            return int(raw_text)
        except ValueError:
            return previous_value
    if isinstance(previous_value, float):
        try:
            return float(raw_text)
        except ValueError:
            return previous_value
    if isinstance(previous_value, (dict, list)):
        try:
            return json.loads(raw_text)
        except ValueError:
            return previous_value
    return raw_text


class AdvancedModeScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._inputs = {}
        self._status_label = None
        self._build_ui()

    def on_pre_enter(self):
        # Re-read from the store every time the screen is shown, in case
        # something changed elsewhere (e.g. onboarding just ran).
        self._refresh_values()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        back_btn = Button(text="< Back", size_hint=(1, None), height=dp(44), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "settings"))
        root.add_widget(back_btn)

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(56))
        header.add_widget(Label(
            text="Advanced mode",
            font_size="20sp",
            bold=True,
            halign="left",
            size_hint_y=None,
            height=dp(28),
        ))
        header.add_widget(Label(
            text="Direct system configuration. Changes apply immediately on save.",
            font_size="12sp",
            color=(0.6, 0.63, 0.67, 1),
            halign="left",
            size_hint_y=None,
            height=dp(20),
        ))
        root.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=2, spacing=dp(8), padding=dp(4), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for key in EDITABLE_KEYS:
            grid.add_widget(Label(
                text=key,
                font_size="13sp",
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(40),
            ))
            field = TextInput(
                text="",
                multiline=False,
                font_size="13sp",
                size_hint_y=None,
                height=dp(40),
            )
            self._inputs[key] = field
            grid.add_widget(field)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(10))
        self._status_label = Label(text="", font_size="12sp", color=(0.3, 0.85, 0.75, 1))
        actions.add_widget(self._status_label)
        actions.add_widget(Button(text="Reload", size_hint_x=None, width=dp(110), on_release=lambda *_: self._refresh_values()))
        actions.add_widget(Button(text="Save changes", size_hint_x=None, width=dp(140), on_release=lambda *_: self._save_all()))
        root.add_widget(actions)

        self.add_widget(root)

    def _refresh_values(self):
        for key, field in self._inputs.items():
            value = store.get(key)
            if isinstance(value, (dict, list)):
                field.text = json.dumps(value)
            elif value is None:
                field.text = ""
            else:
                field.text = str(value)
        self._status_label.text = ""

    def _save_all(self):
        changed = []
        for key, field in self._inputs.items():
            previous = store.get(key)
            new_value = _coerce(field.text, previous)
            if new_value != previous:
                store.set(key, new_value)
                changed.append(key)
        self._status_label.text = (
            f"Saved ({len(changed)} changed)" if changed else "No changes"
        )
