"""
Speedometer + location: real speed and position from the phone's GPS.
No extra hardware needed, works in literally any car.

Reports both speed (for the dashboard gauge) and lat/lon (for toll
geofencing and speed-limit lookup), so one GPS subscription serves all
three features instead of three separate ones draining battery.
"""

from kivy.utils import platform
from kivy.clock import Clock


class SpeedTracker:
    def __init__(self, on_speed_update, on_location_update=None):
        self.on_speed_update = on_speed_update            # callback(speed_kmh: float)
        self.on_location_update = on_location_update       # callback(lat, lon, speed_kmh)
        self._location_manager = None
        self._listener = None

    def start(self):
        if platform != "android":
            # Desktop dev fallback: fake movement so gauges/toll/speed-limit
            # logic can be tested without a phone. Starts near a made-up
            # point and drifts, with speed oscillating realistically.
            self._sim_speed = 0.0
            self._sim_lat = 28.6139
            self._sim_lon = 77.2090
            Clock.schedule_interval(self._simulate, 1.0)
            return

        try:
            from jnius import autoclass, PythonJavaClass, java_method
            from android.permissions import request_permissions, Permission

            request_permissions(
                [Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION]
            )

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            LocationManager = autoclass("android.location.LocationManager")

            activity = PythonActivity.mActivity
            self._location_manager = activity.getSystemService(Context.LOCATION_SERVICE)

            outer = self

            class LocListener(PythonJavaClass):
                __javainterfaces__ = ["android/location/LocationListener"]
                __javacontext__ = "app"

                @java_method("(Landroid/location/Location;)V")
                def onLocationChanged(self, location):
                    speed_mps = location.getSpeed()
                    speed_kmh = round(speed_mps * 3.6, 1)
                    lat = location.getLatitude()
                    lon = location.getLongitude()

                    outer.on_speed_update(speed_kmh)
                    if outer.on_location_update:
                        outer.on_location_update(lat, lon, speed_kmh)

                @java_method("(Ljava/lang/String;)V")
                def onProviderEnabled(self, provider):
                    pass

                @java_method("(Ljava/lang/String;)V")
                def onProviderDisabled(self, provider):
                    pass

                @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
                def onStatusChanged(self, provider, status, extras):
                    pass

            self._listener = LocListener()
            self._location_manager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER, 1000, 1, self._listener
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Speed tracker start failed: {exc}")

    def _simulate(self, dt):
        import random

        self._sim_speed = max(0, min(120, self._sim_speed + random.uniform(-3, 4)))
        # drift position slightly to simulate driving
        self._sim_lat += random.uniform(-0.0005, 0.0005)
        self._sim_lon += random.uniform(-0.0005, 0.0005)

        speed = round(self._sim_speed, 1)
        self.on_speed_update(speed)
        if self.on_location_update:
            self.on_location_update(self._sim_lat, self._sim_lon, speed)

    def stop(self):
        if self._location_manager and self._listener:
            try:
                self._location_manager.removeUpdates(self._listener)
            except Exception:
                pass
