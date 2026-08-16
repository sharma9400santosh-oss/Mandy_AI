"""
warning_rail.py — the dashboard warning-light rail from the browser
prototype (oil / tire / battery / brake), rebuilt as a real Kivy widget.

Confirmed by inspecting the app: there's no existing warning-light concept
anywhere in v10 — bottom_bar.py is a pinned-app shortcut bar, and the
existing image assets (icon_apps, icon_calls, icon_camera, icon_connectivity,
icon_dashboard, icon_docs, icon_files, icon_media, icon_navigate,
icon_settings, icon_trip, mandy_face) don't include warning icons. This
package ships four new ones under assets/ (icon_warn_oil.png,
icon_warn_tire.png, icon_warn_battery.png, icon_warn_brake.png) styled to
match the amber warning-light look from the prototype.

Each icon lights up (amber ring) when `set_fault(key, True)` is called —
wire that to whatever already watches OBD data (climate_alert.py,
speed_limit_tracker.py, or a periodic Mode 01 poll) plus the new Mode 03
DTC reader for anything that isn't a simple threshold check. Tapping a lit
or unlit icon both trigger the same live diagnostic explanation — tapping
an unlit icon is just "check now" on demand.

Usage (dashboard_screen.py):

    from warning_rail import WarningRail

    self.warning_rail = WarningRail(
        on_icon_pressed=self._on_warning_pressed,
    )
    self.add_widget(self.warning_rail)

    def _on_warning_pressed(self, key):
        self.explainer.explain(self.obd_reader._socket, user_name=store.get('user_name'))

    # elsewhere, whenever you detect an anomaly:
    self.warning_rail.set_fault('oil', True)
"""

import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Line
from kivy.metrics import dp

_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

_ICONS = [
    ("oil", "icon_warn_oil.png"),
    ("tire", "icon_warn_tire.png"),
    ("battery", "icon_warn_battery.png"),
    ("brake", "icon_warn_brake.png"),
]

_FAULT_RING = (0.96, 0.65, 0.14, 1)
_IDLE_RING = (1, 1, 1, 0.12)


class _WarningIcon(ButtonBehavior, BoxLayout):
    def __init__(self, key, icon_path, on_press_cb, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self._on_press_cb = on_press_cb
        self._fault = False

        self._ring_color = Color(*_IDLE_RING)
        with self.canvas.before:
            self.canvas.before.add(self._ring_color)
            self._ring_line = Line(width=2.5)

        self.add_widget(Image(source=icon_path, allow_stretch=True, keep_ratio=True))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        cx, cy = self.center_x, self.center_y
        radius = min(self.width, self.height) * 0.48
        self._ring_line.circle = (cx, cy, radius)

    def on_press(self):
        if self._on_press_cb:
            self._on_press_cb(self.key)

    def set_fault(self, is_fault):
        self._fault = is_fault
        self._ring_color.rgba = _FAULT_RING if is_fault else _IDLE_RING


class WarningRail(BoxLayout):
    def __init__(self, on_icon_pressed=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", dp(12))
        kwargs.setdefault("padding", dp(8))
        super().__init__(**kwargs)
        self._icons = {}

        for key, filename in _ICONS:
            icon_path = os.path.join(_ASSET_DIR, filename)
            icon = _WarningIcon(
                key=key,
                icon_path=icon_path,
                on_press_cb=on_icon_pressed,
                size_hint=(1, None),
                height=dp(44),
            )
            self._icons[key] = icon
            self.add_widget(icon)

    def set_fault(self, key, is_fault):
        icon = self._icons.get(key)
        if icon:
            icon.set_fault(is_fault)

    def any_fault(self):
        return any(icon._fault for icon in self._icons.values())
