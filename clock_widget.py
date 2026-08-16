"""
Live clock + date display, respecting the 12h/24h format choice in
Settings.
"""

from datetime import datetime

from kivy.uix.label import Label
from kivy.clock import Clock

import settings_store as store


class ClockWidget(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update(0)
        Clock.schedule_interval(self._update, 1.0)

    def _update(self, dt):
        now = datetime.now()
        use_24h = store.get("time_format_24h")
        time_str = now.strftime("%H:%M:%S") if use_24h else now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%a, %d %b %Y")
        self.text = f"{time_str}\n{date_str}"
