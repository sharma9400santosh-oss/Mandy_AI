from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from navigation import launch_navigation


class NavigateScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", padding=16, spacing=12)

        back_btn = Button(text="< Back", size_hint=(1, 0.1), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back_btn)

        root.add_widget(Label(text="Navigation", font_size="24sp", size_hint=(1, 0.15)))

        self.dest_input = TextInput(
            hint_text="Type a destination (or just use voice on Home)",
            size_hint=(1, 0.15),
            multiline=False,
        )
        root.add_widget(self.dest_input)

        go_btn = Button(text="Start Navigation", font_size="20sp", size_hint=(1, 0.2),
                         background_color=(0.2, 0.5, 0.9, 1))
        go_btn.bind(on_press=self._go)
        root.add_widget(go_btn)

        self.status_label = Label(text="", font_size="14sp", size_hint=(1, 0.2))
        root.add_widget(self.status_label)

        self.add_widget(root)

    def _go(self, *_):
        destination = self.dest_input.text.strip()
        if not destination:
            self.status_label.text = "Type a destination first."
            return
        launch_navigation(destination)
        self.status_label.text = f"Navigating to {destination}..."
