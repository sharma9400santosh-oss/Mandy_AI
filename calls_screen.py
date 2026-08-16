from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from call_manager import call_contact


class CallsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", padding=16, spacing=12)

        back_btn = Button(text="< Back", size_hint=(1, 0.1), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back_btn)

        root.add_widget(Label(text="Calls", font_size="24sp", size_hint=(1, 0.15)))

        self.name_input = TextInput(
            hint_text="Contact name or phone number",
            size_hint=(1, 0.15),
            multiline=False,
        )
        root.add_widget(self.name_input)

        call_btn = Button(text="Call", font_size="20sp", size_hint=(1, 0.2),
                           background_color=(0.15, 0.7, 0.3, 1))
        call_btn.bind(on_press=self._do_call)
        root.add_widget(call_btn)

        self.status_label = Label(text="", font_size="14sp", size_hint=(1, 0.2))
        root.add_widget(self.status_label)

        self.add_widget(root)

    def _do_call(self, *_):
        target = self.name_input.text.strip()
        if not target:
            self.status_label.text = "Enter a name or number first."
            return
        result = call_contact(target)
        self.status_label.text = result
