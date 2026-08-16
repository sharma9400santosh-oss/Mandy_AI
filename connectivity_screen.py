"""
Connectivity screen: Wi-Fi status (read-only) and Bluetooth connection
to your car (reuses the existing bluetooth_manager.py).
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import mainthread

from bluetooth_manager import BluetoothManager
import wifi_manager


class ConnectivityScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bt_manager = BluetoothManager(on_status_change=self._on_bt_status)

        root = BoxLayout(orientation="vertical", padding=16, spacing=14)

        back_btn = Button(text="< Back", size_hint=(1, 0.1), font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back_btn)

        root.add_widget(Label(text="Connectivity", font_size="22sp", size_hint=(1, 0.12)))

        # ---- Wi-Fi ----
        root.add_widget(Label(text="Wi-Fi", font_size="16sp", size_hint=(1, 0.08)))
        self.wifi_status_label = Label(text="Not checked yet", font_size="14sp",
                                        color=(0.75, 0.75, 0.75, 1), size_hint=(1, 0.1))
        root.add_widget(self.wifi_status_label)
        wifi_check_btn = Button(text="Check Wi-Fi Status", size_hint=(1, 0.12),
                                 background_color=(0.2, 0.55, 0.8, 1))
        wifi_check_btn.bind(on_press=self._check_wifi)
        root.add_widget(wifi_check_btn)

        # ---- Bluetooth ----
        root.add_widget(Label(text="Bluetooth", font_size="16sp", size_hint=(1, 0.08)))
        self.bt_status_label = Label(text="Not connected", font_size="14sp",
                                      color=(0.75, 0.75, 0.75, 1), size_hint=(1, 0.1))
        root.add_widget(self.bt_status_label)
        bt_connect_btn = Button(text="Connect to Vehicle Bluetooth", size_hint=(1, 0.12),
                                 background_color=(0.2, 0.55, 0.8, 1))
        bt_connect_btn.bind(on_press=self._connect_bluetooth)
        root.add_widget(bt_connect_btn)

        root.add_widget(Label(
            text="Note: Android reserves actually turning Wi-Fi/Bluetooth on or off, "
                 "or connecting to a new network, to its own Settings app for security "
                 "reasons -- this screen can check status and connect to already-paired "
                 "Bluetooth devices, not silently change your connections.",
            font_size="11sp", color=(0.6, 0.6, 0.6, 1), size_hint=(1, 0.2)))

        self.add_widget(root)

    def _check_wifi(self, *_):
        self.wifi_status_label.text = "Checking..."
        status = wifi_manager.get_wifi_status()
        self.wifi_status_label.text = status

    def _connect_bluetooth(self, *_):
        self.bt_status_label.text = "Searching..."
        import threading
        threading.Thread(target=self.bt_manager.connect, daemon=True).start()

    @mainthread
    def _on_bt_status(self, status_text):
        self.bt_status_label.text = status_text
