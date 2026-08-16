"""
Onboarding screen: shown once, on first launch, before the main app.
Asks for a phone number and a name, then unlocks the rest of the app.

HONEST SCOPE: this is NOT a login or security check. There's no OTP, no
server-side verification -- it just requires *something* to be entered
before continuing, and stores it locally. Real phone verification would
need a paid SMS/auth service (Firebase Auth, Twilio, etc.) running on a
server you maintain -- a much bigger, ongoing-cost feature. This screen
is a one-time local setup step, not an account system.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

import settings_store as store


class OnboardingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", padding=40, spacing=16)

        root.add_widget(Label(
            text="Welcome to Mandy",
            font_size="28sp", size_hint=(1, 0.2)
        ))
        root.add_widget(Label(
            text="Set up your profile to get started.\n"
                 "(This is stored only on this device -- not a login,\n"
                 "just how Mandy will address you and keep your info.)",
            font_size="13sp", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.2)
        ))

        root.add_widget(Label(text="Your name", font_size="14sp", size_hint=(1, 0.08)))
        self.name_input = TextInput(
            hint_text="e.g. Santosh", multiline=False, font_size="16sp",
            size_hint=(1, 0.12),
        )
        root.add_widget(self.name_input)

        root.add_widget(Label(text="Phone number", font_size="14sp", size_hint=(1, 0.08)))
        self.phone_input = TextInput(
            hint_text="e.g. +91 98765 43210", multiline=False, font_size="16sp",
            size_hint=(1, 0.12), input_type="tel",
        )
        root.add_widget(self.phone_input)

        self.error_label = Label(
            text="", font_size="13sp", color=(0.9, 0.4, 0.4, 1), size_hint=(1, 0.08)
        )
        root.add_widget(self.error_label)

        continue_btn = Button(
            text="Continue", font_size="18sp", size_hint=(1, 0.18),
            background_color=(0.2, 0.55, 0.85, 1),
        )
        continue_btn.bind(on_press=self._on_continue)
        root.add_widget(continue_btn)

        self.add_widget(root)

    def _on_continue(self, *_):
        name = self.name_input.text.strip()
        phone = self.phone_input.text.strip()
        digits = "".join(ch for ch in phone if ch.isdigit())

        if not name:
            self.error_label.text = "Please enter your name."
            return
        if len(digits) < 8:
            self.error_label.text = "Please enter a valid phone number."
            return

        store.set("user_name", name)
        store.set("owner_phone", phone)
        store.set("onboarding_complete", True)

        # HomeScreen's conversation engine was created before onboarding
        # ran (all screens are built at app startup) -- push the name in
        # now so Mandy addresses you correctly from the very first use.
        home_screen = self.manager.get_screen("home")
        home_screen.conversation.user_name = name

        self.manager.current = "home"
