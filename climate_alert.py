"""
Climate alert: suggests adjusting your AC/heater based on ambient
(outside) temperature -- see the note in obd_reader.py for why this
uses ambient temp rather than actual cabin/AC state (that data isn't
available through the standard OBD-II protocol).

Thresholds are configurable in Settings. Defaults are reasonable for
most climates but you may want to tune them for where you drive.
"""

import settings_store as store

DEFAULT_HIGH_C = 32.0
DEFAULT_LOW_C = 10.0


def check_temperature(ambient_c: float):
    """Returns an alert message string, or None if temperature is in a
    comfortable range."""
    high = float(store.get("climate_alert_high_c") or DEFAULT_HIGH_C)
    low = float(store.get("climate_alert_low_c") or DEFAULT_LOW_C)

    if ambient_c >= high:
        return f"It's {ambient_c:.0f}°C outside -- consider turning on the AC."
    if ambient_c <= low:
        return f"It's {ambient_c:.0f}°C outside -- consider turning on the heater."
    return None
