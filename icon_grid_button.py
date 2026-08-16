"""
Icon-based app grid button: icon image on top, label underneath. Used on
the Home screen dashboard grid (Media, Calls, Navigate, Docs, Files,
Settings, Connectivity).

The ENTIRE tile is tappable (via ButtonBehavior on the container), not
just the small text label -- tapping the icon graphic itself now works,
which is what people naturally try to tap first.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle


class IconGridButton(ButtonBehavior, BoxLayout):
    def __init__(self, icon_path, label_text, on_press, **kwargs):
        super().__init__(orientation="vertical", spacing=2, **kwargs)
        self._on_press_callback = on_press

        # Subtle background so the whole tappable area is visually obvious,
        # and gives a pressed-state highlight.
        with self.canvas.before:
            self._bg_color = Color(0.13, 0.13, 0.17, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        icon = Image(source=icon_path, size_hint=(1, 0.72), allow_stretch=True)
        self.add_widget(icon)

        label = Label(text=label_text, size_hint=(1, 0.28), font_size="12sp")
        self.add_widget(label)

    def _update_bg(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_press(self):
        self._bg_color.rgba = (0.25, 0.35, 0.55, 1)  # brief highlight on tap
        self._on_press_callback()

    def on_release(self):
        self._bg_color.rgba = (0.13, 0.13, 0.17, 1)
