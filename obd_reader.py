"""
OBD-II reader: real RPM, fuel level, and ambient (outside) temperature
via a Bluetooth ELM327 adapter plugged into your car's OBD-II port.

REQUIRES HARDWARE: a ~$10-15 Bluetooth ELM327 dongle. Without one
plugged in, none of this data is available -- there is no way around
that; regular car Bluetooth (the audio/hands-free kind) does not expose
engine data, only the OBD-II port does. This works with any OBD-II
compliant vehicle (legally required in most countries since the
mid-2000s) since it uses the standardized public PID list -- no
vehicle-specific setup needed once an adapter is paired.

COVERAGE VARIES BY VEHICLE: not every car reports every PID. Fuel
level and ambient temperature especially are commonly-but-not-always
supported -- if your car doesn't report one, that reading just stays
unavailable, which is expected, not a bug.

WHAT THIS CANNOT DO: read actual cabin/AC temperature or control state.
That's set by each manufacturer's own proprietary HVAC system with
undocumented, brand-and-model-specific codes -- not part of the public
OBD-II standard. This uses ambient (outside) air temperature (a real,
standardized PID) as the closest available signal for a "should I
adjust the AC" alert -- see climate_alert.py.

Protocol summary: ELM327 acts as a classic Bluetooth SPP (serial) device.
We send AT commands to initialize it, then send OBD PID requests like
"010C" (engine RPM) and parse the hex response.
"""

from kivy.utils import platform
from kivy.clock import Clock

RPM_PID = "010C"
SPEED_PID = "010D"  # (backup/cross-check vs GPS speed)
FUEL_LEVEL_PID = "012F"
AMBIENT_TEMP_PID = "0146"

# Broadened from just "obd"/"elm" -- common cheap ELM327 clones use a
# variety of Bluetooth names that don't necessarily include either word.
ADAPTER_NAME_KEYWORDS = [
    "obd", "elm", "obdii", "obd2", "obd-ii", "vgate", "konnwei",
    "v-link", "vlink", "veepeak", "bafx", "carista", "torque",
]


class OBDReader:
    def __init__(self, on_rpm_update, on_status_change,
                 on_fuel_update=None, on_temp_update=None):
        self.on_rpm_update = on_rpm_update
        self.on_status_change = on_status_change
        self.on_fuel_update = on_fuel_update
        self.on_temp_update = on_temp_update
        self._socket = None
        self._connected = False
        self._poll_count = 0  # used to stagger RPM/fuel/temp polling

    def connect(self):
        if platform != "android":
            self.on_status_change("OBD only available on Android device")
            self._simulate()
            return

        try:
            from jnius import autoclass

            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            UUID = autoclass("java.util.UUID")

            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None or not adapter.isEnabled():
                self.on_status_change("Bluetooth not available/enabled")
                return

            paired = adapter.getBondedDevices().toArray()
            target = None
            for device in paired:
                name = (device.getName() or "").lower()
                if any(keyword in name for keyword in ADAPTER_NAME_KEYWORDS):
                    target = device
                    break

            if target is None:
                self.on_status_change(
                    "No paired OBD adapter found. Pair your ELM327 dongle "
                    "in phone Bluetooth settings first."
                )
                return

            spp_uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
            self._socket = target.createRfcommSocketToServiceRecord(spp_uuid)
            self._socket.connect()
            self._connected = True
            self.on_status_change(f"connected to {target.getName()}")

            self._send_at("ATZ")   # reset
            self._send_at("ATE0")  # echo off
            self._send_at("ATSP0")  # auto protocol

            Clock.schedule_interval(self._poll, 0.5)

        except Exception as exc:  # noqa: BLE001
            self.on_status_change(f"OBD connection failed: {exc}")

    def _send_at(self, command):
        if not self._socket:
            return None
        try:
            out = self._socket.getOutputStream()
            out.write((command + "\r").encode())
            out.flush()
        except Exception as exc:  # noqa: BLE001
            print(f"OBD command failed: {exc}")

    def _query_pid(self, pid: str):
        out = self._socket.getOutputStream()
        out.write((pid + "\r").encode())
        out.flush()

        inp = self._socket.getInputStream()
        buffer = bytearray()
        while True:
            b = inp.read()
            if b in (-1, 0x3E):  # '>' prompt marks end of response
                break
            buffer.append(b)
        return bytes(buffer).decode(errors="ignore")

    def _poll(self, dt):
        if not self._connected:
            return False
        try:
            # RPM every cycle (needs to feel responsive); fuel and
            # temperature every 3rd cycle (they change slowly, no need
            # to hammer the adapter for them).
            self._poll_count += 1

            response = self._query_pid(RPM_PID)
            rpm = self._parse_pid_value(response, "0C", scale=lambda a, b: ((a * 256) + b) / 4)
            if rpm is not None:
                self.on_rpm_update(int(rpm))

            if self._poll_count % 3 == 0:
                if self.on_fuel_update:
                    fuel_response = self._query_pid(FUEL_LEVEL_PID)
                    fuel_pct = self._parse_pid_value(
                        fuel_response, "2F", scale=lambda a, b: (a * 100) / 255
                    )
                    if fuel_pct is not None:
                        self.on_fuel_update(round(fuel_pct, 1))

                if self.on_temp_update:
                    temp_response = self._query_pid(AMBIENT_TEMP_PID)
                    temp_c = self._parse_pid_value(
                        temp_response, "46", scale=lambda a, b: a - 40
                    )
                    if temp_c is not None:
                        self.on_temp_update(temp_c)

        except Exception as exc:  # noqa: BLE001
            print(f"OBD poll failed: {exc}")
        return True

    @staticmethod
    def _parse_pid_value(response: str, pid_byte: str, scale):
        # Expected reply looks like: "41 0C 1A F8" -> value via `scale(A, B)`
        hex_bytes = [b for b in response.replace("\r", " ").split(" ") if b]
        try:
            idx = hex_bytes.index(pid_byte)
            a = int(hex_bytes[idx + 1], 16)
            b = int(hex_bytes[idx + 2], 16) if idx + 2 < len(hex_bytes) else 0
            return scale(a, b)
        except (ValueError, IndexError):
            return None

    def _simulate(self):
        """Desktop dev fallback so the gauge UI can be built/tested
        without a car or OBD adapter."""
        import random

        self._sim_rpm = 800
        self._sim_fuel = 72.0
        self._sim_temp = 32.0

        def tick(dt):
            self._sim_rpm = max(700, min(6000, self._sim_rpm + random.uniform(-150, 180)))
            self.on_rpm_update(int(self._sim_rpm))
            if self.on_fuel_update:
                self._sim_fuel = max(0, self._sim_fuel - random.uniform(0, 0.05))
                self.on_fuel_update(round(self._sim_fuel, 1))
            if self.on_temp_update:
                self._sim_temp += random.uniform(-0.3, 0.3)
                self.on_temp_update(round(self._sim_temp, 1))

        Clock.schedule_interval(tick, 0.5)
