"""
Mandy's avatar: her face, with a glowing ring that animates depending on
her state (idle / listening / thinking / speaking). This is what makes
her feel present rather than just a UI with a mic button.
"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Line, Ellipse
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import StringProperty

STATE_COLORS = {
    "idle": (0.3, 0.6, 0.9, 0.5),       # calm blue
    "listening": (0.2, 0.9, 0.6, 0.9),  # active green
    "thinking": (0.9, 0.7, 0.2, 0.8),   # amber
    "speaking": (0.85, 0.3, 0.75, 0.9), # warm pink (matches her hair!)
    "concerned": (0.9, 0.35, 0.3, 0.9), # for stressed/urgent tone back to user
}


class MandyAvatar(FloatLayout):
    state = StringProperty("idle")

    def __init__(self, face_source, **kwargs):
        super().__init__(**kwargs)
        self._pulse_anim = None

        self.face = Image(
            source=face_source,
            size_hint=(0.9, 0.9),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            allow_stretch=True,
            keep_ratio=True,
        )
        self.add_widget(self.face)

        with self.canvas.before:
            self._glow_color = Color(*STATE_COLORS["idle"])
            self._glow_line = Line(width=3)

        self.bind(size=self._redraw_glow, pos=self._redraw_glow)
        Clock.schedule_once(lambda dt: self._redraw_glow(), 0)
        self.set_state("idle")

    def _redraw_glow(self, *_):
        cx = self.center_x
        cy = self.center_y
        radius = min(self.width, self.height) * 0.46
        self._glow_line.circle = (cx, cy, radius)

    def set_state(self, new_state: str):
        """Switch Mandy's visual state and animate the glow accordingly."""
        self.state = new_state
        color = STATE_COLORS.get(new_state, STATE_COLORS["idle"])

        if self._pulse_anim:
            self._pulse_anim.cancel(self._glow_color)

        target = Color(*color)
        anim = Animation(rgba=color, duration=0.4)

        if new_state in ("listening", "speaking"):
            pulse = Animation(rgba=(color[0], color[1], color[2], 0.4), duration=0.6) + \
                    Animation(rgba=color, duration=0.6)
            anim = anim + pulse
            anim.repeat = True

        self._pulse_anim = anim
        anim.start(self._glow_color)
