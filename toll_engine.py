"""
Toll engine: watches your live GPS position and alerts you when
approaching a known toll plaza, with its price.

IMPORTANT: the bundled `assets/toll_database.json` is EXAMPLE data, not
a real, current, national toll database -- there is no free/reliable
live source I can bake in that's guaranteed accurate. For this to be
genuinely useful, replace the entries in that file with real toll
plazas along your regular routes (name, lat/lon, radius, and prices
per vehicle class), sourced from NHAI's official FASTag toll list.
"""

import json
import math
import time

DB_PATH = "assets/toll_database.json"
RE_ALERT_COOLDOWN_SECONDS = 600  # don't re-alert for the same plaza for 10 min


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (math.sin(d_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


class TollEngine:
    def __init__(self, on_toll_approaching, vehicle_class="car", db_path=DB_PATH):
        """
        on_toll_approaching(name: str, price: int|None, vehicle_class: str)
        """
        self.on_toll_approaching = on_toll_approaching
        self.vehicle_class = vehicle_class
        self._tolls = self._load_db(db_path)
        self._last_alerted = {}  # name -> timestamp

    def _load_db(self, path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return data.get("tolls", [])
        except Exception as exc:  # noqa: BLE001
            print(f"Toll database load failed: {exc}")
            return []

    def update_location(self, lat, lon):
        now = time.time()
        for toll in self._tolls:
            distance = _haversine_m(lat, lon, toll["lat"], toll["lon"])
            if distance <= toll.get("radius_m", 500):
                last = self._last_alerted.get(toll["name"], 0)
                if now - last > RE_ALERT_COOLDOWN_SECONDS:
                    self._last_alerted[toll["name"]] = now
                    price = toll.get("prices", {}).get(self.vehicle_class)
                    self.on_toll_approaching(toll["name"], price, self.vehicle_class)
