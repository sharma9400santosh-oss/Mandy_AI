"""
Camera screen: live preview from your phone's camera.

IMPORTANT SCOPE NOTE (read this before wondering where the 360-degree
view is): a genuine 360-degree surround view, like OEM around-view
monitor systems, needs MULTIPLE physical cameras mounted around the
vehicle (front/rear/left/right) feeding a dedicated stitching
processor. A phone running one app cannot produce that on its own --
there's no way to synthesize views of the sides of your car from a
single camera. What this screen gives you instead: a live feed from
whichever camera your phone has (front or back), which is useful on
its own (e.g. mounted facing forward or as a rear-view aid), but it is
one camera's view, not a stitched 360-degree composite.

If you have an actual car camera system (a proper reversing camera or
a 360-camera kit), integrating with it would need that system's own
(usually undocumented, brand-specific) video output -- not something
this generic app can support.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

try:
    from kivy.uix.camera import Camera
    CAMERA_AVAILABLE = True
except Exception:  # noqa: BLE001
    CAMERA_AVAILABLE = False


class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._camera_widget = None
        self._current_index = 0

        self.root_layout = BoxLayout(orientation="vertical", padding=16, spacing=10)

        back_btn = Button(text="< Back", size_hint=(1, 0.08), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        self.root_layout.add_widget(back_btn)

        self.root_layout.add_widget(Label(
            text="Live camera preview -- single camera, not 360-degree "
                 "(see note in the code/README for why)",
            font_size="12sp", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.08)
        ))

        self.camera_container = BoxLayout(size_hint=(1, 0.72))
        self.root_layout.add_widget(self.camera_container)

        switch_btn = Button(text="Switch Front/Back Camera", size_hint=(1, 0.12),
                             background_color=(0.2, 0.55, 0.85, 1))
        switch_btn.bind(on_press=self._switch_camera)
        self.root_layout.add_widget(switch_btn)

        self.add_widget(self.root_layout)

    def on_enter(self, *_):
        self._start_camera()

    def on_leave(self, *_):
        self._stop_camera()

    def _start_camera(self):
        if not CAMERA_AVAILABLE:
            self.camera_container.clear_widgets()
            self.camera_container.add_widget(Label(
                text="Camera preview isn't available in this build."
            ))
            return

        self.camera_container.clear_widgets()
        try:
            self._camera_widget = Camera(
                index=self._current_index, resolution=(640, 480), play=True
            )
            self.camera_container.add_widget(self._camera_widget)
        except Exception as exc:  # noqa: BLE001
            self.camera_container.add_widget(Label(text=f"Camera error: {exc}"))

    def _stop_camera(self):
        if self._camera_widget:
            self._camera_widget.play = False
            self._camera_widget = None

    def _switch_camera(self, *_):
        self._current_index = 1 - self._current_index
        self._start_camera()
