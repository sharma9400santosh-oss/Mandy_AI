"""
Trip computer: tracks distance driven (via GPS, works in any car) and,
if you have an OBD-II adapter connected, estimates fuel level and
km-per-litre.

HONEST SCOPE:
- Distance driven: reliable, GPS-only, no extra hardware needed.
- Fuel level: only available if your OBD-II adapter is connected AND
  your specific vehicle exposes PID 012F (fuel tank level). Coverage
  varies a lot by make/model/year -- some report it accurately, some
  not at all. EVs generally do NOT expose battery charge over this
  generic PID; that needs manufacturer-specific protocols this app
  doesn't implement.
- km/l estimate: calculated from (fuel % dropped x tank capacity you
  enter in Settings) / (km driven since last fuel reading). This is a
  rough estimate, not a certified fuel economy reading -- fuel level
  sensors are typically low-resolution and noisy over short distances.
"""

import math

import settings_store as store

EARTH_RADIUS_M = 6371000


def _haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (math.sin(d_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    return (2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))) / 1000.0


class TripComputer:
    def __init__(self):
        self._last_lat = None
        self._last_lon = None
        self._trip_km = float(store.get("trip_km_total") or 0.0)

        self._last_fuel_pct = None
        self._fuel_pct_at_trip_start = None
        self._km_at_last_fuel_reading = 0.0

    def update_location(self, lat, lon):
        if self._last_lat is not None:
            delta_km = _haversine_km(self._last_lat, self._last_lon, lat, lon)
            # Ignore GPS jitter (sudden jumps while stationary).
            if 0 < delta_km < 1.0:
                self._trip_km += delta_km
                store.set("trip_km_total", self._trip_km)
        self._last_lat, self._last_lon = lat, lon

    def get_trip_km(self):
        return round(self._trip_km, 2)

    def reset_trip(self):
        self._trip_km = 0.0
        store.set("trip_km_total", 0.0)
        self._km_at_last_fuel_reading = self._trip_km
        self._fuel_pct_at_trip_start = self._last_fuel_pct

    def update_fuel_level(self, fuel_pct):
        """Call this with fresh OBD fuel-level readings (0-100)."""
        if self._fuel_pct_at_trip_start is None:
            self._fuel_pct_at_trip_start = fuel_pct
            self._km_at_last_fuel_reading = self._trip_km
        self._last_fuel_pct = fuel_pct

    def get_fuel_pct(self):
        return self._last_fuel_pct  # None if no OBD fuel data yet

    def get_estimated_km_per_litre(self):
        """Returns a float, or None if not enough data yet."""
        if self._last_fuel_pct is None or self._fuel_pct_at_trip_start is None:
            return None

        tank_capacity = float(store.get("fuel_tank_capacity_l") or 0)
        if tank_capacity <= 0:
            return None  # user hasn't entered their tank size in Settings

        pct_used = self._fuel_pct_at_trip_start - self._last_fuel_pct
        km_driven = self._trip_km - self._km_at_last_fuel_reading

        if pct_used <= 0.5 or km_driven <= 0.5:
            return None  # not enough fuel drop / distance yet for a meaningful estimate

        litres_used = (pct_used / 100.0) * tank_capacity
        if litres_used <= 0:
            return None

        return round(km_driven / litres_used, 1)
