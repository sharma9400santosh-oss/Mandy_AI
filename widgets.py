"""
Simple circular gauge widget, used for both the speedometer and the
RPM dial on the dashboard screen.
"""

import math
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty, StringProperty


class Gauge(Widget):
    value = NumericProperty(0)
    max_value = NumericProperty(100)
    unit = StringProperty("")

    def __init__(self, max_value=100, unit="", accent=(0.2, 0.7, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.max_value = max_value
        self.unit = unit
        self.accent = accent

        self.value_label = Label(font_size="32sp", bold=True)
        self.unit_label = Label(text=unit, font_size="14sp", color=(0.7, 0.7, 0.7, 1))
        self.add_widget(self.value_label)
        self.add_widget(self.unit_label)

        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)

    def set_value(self, value):
        self.value = max(0, min(value, self.max_value))

    def _redraw(self, *_):
        self.canvas.after.clear()
        cx, cy = self.center_x, self.center_y
        radius = min(self.width, self.height) * 0.42
        start_angle = 135
        end_angle = -135  # sweeps 270 degrees total, clockwise

        fraction = self.value / self.max_value if self.max_value else 0
        sweep = start_angle - (start_angle - end_angle) * fraction

        with self.canvas.after:
            # background track
            Color(0.2, 0.2, 0.25, 1)
            Line(circle=(cx, cy, radius, end_angle, start_angle), width=6)
            # value arc
            Color(*self.accent)
            Line(circle=(cx, cy, radius, sweep, start_angle), width=6)

        self.value_label.center = (cx, cy + 10)
        self.value_label.text = str(int(self.value))
        self.unit_label.center = (cx, cy - 20)
