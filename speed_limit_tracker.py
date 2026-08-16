"""
Speed limit tracker: looks up the posted speed limit for the road
you're currently on (via OpenStreetMap's Overpass API, which has
crowd-sourced `maxspeed` tags on many roads) and flags it if your GPS
speed goes over it.

HONEST LIMITATIONS:
- Needs an internet connection -- no offline fallback for real limits.
- OSM's maxspeed coverage is incomplete and crowd-sourced, especially
  outside major highways -- absence of a value doesn't mean "no limit,"
  it usually means nobody's tagged it yet.
- Queries are throttled (every ~20 seconds) to be a respectful, free
  API user and to avoid excessive mobile data use -- this means the
  limit shown can lag a few seconds behind a limit change on the road.
- This is a convenience indicator, not a certified speed-limit sign
  reader -- don't treat an absence of a warning as confirmation you're
  within a legal limit.
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
QUERY_COOLDOWN_SECONDS = 20
SEARCH_RADIUS_M = 40


class SpeedLimitTracker:
    def __init__(self, on_limit_update, on_over_limit):
        """
        on_limit_update(limit_kmh: int|None): called whenever a fresh
            limit lookup completes (None if no tagged limit found nearby).
        on_over_limit(current_kmh: float, limit_kmh: int): called only
            when current speed exceeds the known limit.
        """
        self.on_limit_update = on_limit_update
        self.on_over_limit = on_over_limit
        self._last_query_time = 0
        self._last_limit = None

    def update(self, lat, lon, current_speed_kmh):
        now = time.time()
        if now - self._last_query_time >= QUERY_COOLDOWN_SECONDS:
            self._last_query_time = now
            self._lookup_limit_async(lat, lon, current_speed_kmh)
        elif self._last_limit is not None and current_speed_kmh > self._last_limit:
            self.on_over_limit(current_speed_kmh, self._last_limit)

    def _lookup_limit_async(self, lat, lon, current_speed_kmh):
        import threading

        threading.Thread(
            target=self._lookup_limit, args=(lat, lon, current_speed_kmh), daemon=True
        ).start()

    def _lookup_limit(self, lat, lon, current_speed_kmh):
        query = f"""
        [out:json][timeout:10];
        way(around:{SEARCH_RADIUS_M},{lat},{lon})["maxspeed"];
        out tags 1;
        """
        try:
            req = urllib.request.Request(
                OVERPASS_URL,
                data=f"data={urllib.parse.quote(query)}".encode(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            limit = None
            for element in data.get("elements", []):
                raw = element.get("tags", {}).get("maxspeed")
                limit = self._parse_maxspeed(raw)
                if limit:
                    break

            self._last_limit = limit
            self.on_limit_update(limit)

            if limit and current_speed_kmh > limit:
                self.on_over_limit(current_speed_kmh, limit)

        except urllib.error.URLError:
            pass  # offline -- silently skip, dashboard just won't show a limit
        except Exception as exc:  # noqa: BLE001
            print(f"Speed limit lookup failed: {exc}")

    @staticmethod
    def _parse_maxspeed(raw):
        if not raw:
            return None
        raw = raw.strip().lower()
        try:
            if "mph" in raw:
                return round(int(raw.split()[0]) * 1.60934)
            return int("".join(ch for ch in raw if ch.isdigit()))
        except (ValueError, IndexError):
            return None
