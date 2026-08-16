"""
Simple persistent settings store (saved to a local JSON file on-device).
"""

from kivy.storage.jsonstore import JsonStore

_STORE_PATH = "mandy_settings.json"
_store = None

DEFAULTS = {
    "api_key": "",
    "wake_phrase": "Mandy, I need you",
    "voice_personality": "Warm & friendly",
    "user_name": "Santosh",
    "voice_profile": "",
    "wake_word_enabled": False,
    "vehicle_number": "BR44T5185",
    "insurer_app_package": "",
    "speed_limit_alerts_enabled": True,
    "owner_phone": "",
    "update_check_repo": "",
    "onboarding_complete": False,
    "fuel_type": "Petrol",
    "fuel_tank_capacity_l": "",
    "time_format_24h": True,
    "trip_km_total": 0.0,
    "vehicle_make": "",
    "vehicle_model": "",
    "climate_alert_high_c": "",
    "climate_alert_low_c": "",
    "climate_alerts_enabled": True,
    "bottom_bar_config": "",
}


def _get_store():
    global _store
    if _store is None:
        _store = JsonStore(_STORE_PATH)
    return _store


def get(key):
    store = _get_store()
    if store.exists(key):
        return store.get(key)["value"]
    return DEFAULTS.get(key, "")


def set(key, value):
    store = _get_store()
    store.put(key, value=value)


def all_settings():
    return {key: get(key) for key in DEFAULTS}
