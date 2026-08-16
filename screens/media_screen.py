from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from media_manager import open_spotify, open_youtube, open_radio


class MediaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", padding=16, spacing=12)

        back_btn = Button(text="< Back", size_hint=(1, 0.1), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back_btn)

        root.add_widget(Label(text="Media", font_size="24sp", size_hint=(1, 0.15)))

        self.search_input = TextInput(
            hint_text="Search a song / video (optional)",
            size_hint=(1, 0.15),
            multiline=False,
        )
        root.add_widget(self.search_input)

        spotify_btn = Button(text="Open Spotify", font_size="18sp", size_hint=(1, 0.15),
                              background_color=(0.11, 0.72, 0.34, 1))
        spotify_btn.bind(on_press=lambda *_: open_spotify(self.search_input.text.strip()))
        root.add_widget(spotify_btn)

        youtube_btn = Button(text="Open YouTube", font_size="18sp", size_hint=(1, 0.15),
                              background_color=(0.8, 0.15, 0.15, 1))
        youtube_btn.bind(on_press=lambda *_: open_youtube(self.search_input.text.strip()))
        root.add_widget(youtube_btn)

        radio_btn = Button(text="Open Radio", font_size="18sp", size_hint=(1, 0.15),
                            background_color=(0.3, 0.4, 0.7, 1))
        radio_btn.bind(on_press=lambda *_: open_radio())
        root.add_widget(radio_btn)

        self.add_widget(root)
