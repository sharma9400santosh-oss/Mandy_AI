"""
Persistent bottom bar: a row of quick-launch shortcuts shown at the
bottom of the Home screen, customizable anytime from Settings.

Stored as a simple ordered list of shortcut keys in settings_store,
e.g. ["dashboard", "spotify", "waze", "whatsapp"]. Each key is either
a built-in screen name (navigates there) or an app_launcher key (opens
that app).
"""

import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

import settings_store as store
import app_launcher

# key -> (label, kind) where kind is "screen" or "app"
AVAILABLE_SHORTCUTS = {
    "dashboard": ("Dashboard", "screen"),
    "media": ("Media", "screen"),
    "calls": ("Calls", "screen"),
    "navigate": ("Navigate", "screen"),
    "documents": ("Docs", "screen"),
    "files": ("Files", "screen"),
    "connectivity": ("Connect", "screen"),
    "apps": ("App Drawer", "screen"),
    "camera": ("Camera", "screen"),
    "settings": ("Settings", "screen"),
    "spotify": ("Spotify", "app"),
    "whatsapp": ("WhatsApp", "app"),
    "waze": ("Waze", "app"),
    "google_maps": ("Google Maps", "app"),
    "youtube_music": ("YT Music", "app"),
    "phonepe": ("PhonePe", "app"),
}

DEFAULT_BOTTOM_BAR = ["dashboard", "media", "navigate", "apps", "settings"]


def get_bottom_bar_config():
    raw = store.get("bottom_bar_config")
    if not raw:
        return list(DEFAULT_BOTTOM_BAR)
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return list(DEFAULT_BOTTOM_BAR)


def set_bottom_bar_config(keys):
    store.set("bottom_bar_config", json.dumps(keys))


class BottomBar(BoxLayout):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(orientation="horizontal", spacing=4, **kwargs)
        self.screen_manager = screen_manager
        self.refresh()

    def refresh(self):
        self.clear_widgets()
        for key in get_bottom_bar_config():
            entry = AVAILABLE_SHORTCUTS.get(key)
            if not entry:
                continue
            label, kind = entry
            btn = Button(text=label, font_size="12sp")
            btn.bind(on_press=lambda inst, k=key, kd=kind: self._activate(k, kd))
            self.add_widget(btn)

    def _activate(self, key, kind):
        if kind == "screen":
            self.screen_manager.current = key
        elif kind == "app":
            app_launcher.open_app(key)
