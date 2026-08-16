"""
App Drawer screen: curated quick-access shortcuts for common apps, plus
a searchable list of every app actually installed on the device.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

import app_launcher
import app_drawer

QUICK_ACCESS = [
    ("Play Store", "play_store"),
    ("Spotify", "spotify"),
    ("YouTube Music", "youtube_music"),
    ("WhatsApp", "whatsapp"),
    ("Waze", "waze"),
    ("Google Maps", "google_maps"),
    ("Assistant", "google_assistant"),
    ("Alexa", "alexa"),
    ("Gmail", "gmail"),
    ("Calendar", "google_calendar"),
    ("PhonePe", "phonepe"),
    ("GPay", "gpay"),
]

SEARCH_SHORTCUTS = [
    ("HERE WeGo", "here_wego"),
    ("MapMyIndia", "mapmyindia"),
    ("Park+", "park_plus"),
    ("IndianOil", "indianoil"),
    ("HPCL", "hpcl"),
    ("BPCL", "bpcl"),
    ("Dashcam (AutoBoy)", "autoboy_dashcam"),
    ("Dashcam (Nexar)", "nexar_dashcam"),
    ("Tata Punch Connect", "tata_punch_connect"),
    ("Bing/MS Copilot", "bing_copilot"),
    ("Weather", "weather"),
    ("TPMS", "tpms"),
]


class AppDrawerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._all_apps = []

        root = BoxLayout(orientation="vertical", padding=16, spacing=10)

        back_btn = Button(text="< Back", size_hint=(1, 0.07), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back_btn)

        root.add_widget(Label(text="Quick Access", font_size="18sp",
                               size_hint=(1, 0.06)))
        quick_grid = GridLayout(cols=4, size_hint=(1, 0.22), spacing=6)
        for label, key in QUICK_ACCESS:
            btn = Button(text=label, font_size="12sp")
            btn.bind(on_press=lambda inst, k=key: app_launcher.open_app(k))
            quick_grid.add_widget(btn)
        root.add_widget(quick_grid)

        root.add_widget(Label(
            text="More apps (opens Play Store search -- exact listing may vary)",
            font_size="12sp", color=(0.65, 0.65, 0.65, 1), size_hint=(1, 0.05)))
        search_grid = GridLayout(cols=4, size_hint=(1, 0.16), spacing=6)
        for label, key in SEARCH_SHORTCUTS:
            btn = Button(text=label, font_size="11sp",
                         background_color=(0.3, 0.3, 0.35, 1))
            btn.bind(on_press=lambda inst, k=key: app_launcher.search_play_store(k))
            search_grid.add_widget(btn)
        root.add_widget(search_grid)

        root.add_widget(Label(text="All Installed Apps", font_size="18sp",
                               size_hint=(1, 0.06)))
        self.filter_input = TextInput(
            hint_text="Type to filter...", multiline=False,
            size_hint=(1, 0.07), font_size="14sp",
        )
        self.filter_input.bind(text=self._on_filter_change)
        root.add_widget(self.filter_input)

        self.scroll = ScrollView(size_hint=(1, 0.31))
        self.apps_list = BoxLayout(orientation="vertical", spacing=2,
                                    size_hint_y=None)
        self.apps_list.bind(minimum_height=self.apps_list.setter("height"))
        self.scroll.add_widget(self.apps_list)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def on_enter(self, *_):
        self._all_apps = app_drawer.list_installed_apps()
        self._render_apps(self._all_apps)

    def _on_filter_change(self, _instance, text):
        text = text.strip().lower()
        if not text:
            self._render_apps(self._all_apps)
            return
        filtered = [a for a in self._all_apps if text in a["label"].lower()]
        self._render_apps(filtered)

    def _render_apps(self, apps):
        self.apps_list.clear_widgets()
        for app in apps:
            btn = Button(text=app["label"], size_hint_y=None, height=42,
                         font_size="13sp", halign="left")
            btn.bind(on_press=lambda inst, pkg=app["package"]: app_drawer.launch_by_package(pkg))
            self.apps_list.add_widget(btn)
