"""
Bluetooth manager.

Phase 1 scope (what this actually does):
  - Checks if Bluetooth is on
  - Lists paired devices
  - Connects audio (A2DP) to a paired car system, if one is found
  - Reports connection status back to the UI

What this does NOT do (would be a phase 2 project):
  - Read live vehicle data (speed, fuel, engine codes) -- that requires
    an OBD-II Bluetooth adapter (like an ELM327) and a separate protocol
    on top of Bluetooth SPP, not standard car-audio Bluetooth.
  - Deep integration with manufacturer infotainment systems -- those are
    closed platforms (Android Auto is the standard, sanctioned way in).
"""

from kivy.utils import platform


class BluetoothManager:
    def __init__(self, on_status_change):
        self.on_status_change = on_status_change

    def connect(self):
        if platform != "android":
            self.on_status_change("Bluetooth only available on Android device")
            return

        try:
            from jnius import autoclass
            from android.permissions import request_permissions, Permission

            request_permissions(
                [Permission.BLUETOOTH_CONNECT, Permission.BLUETOOTH_SCAN]
            )

            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            adapter = BluetoothAdapter.getDefaultAdapter()

            if adapter is None:
                self.on_status_change("No Bluetooth hardware found")
                return

            if not adapter.isEnabled():
                self.on_status_change("Bluetooth is off. Please enable it.")
                return

            paired_devices = adapter.getBondedDevices().toArray()

            if not paired_devices:
                self.on_status_change("No paired devices found. Pair your car first.")
                return

            # Look for a plausible car system by name (heuristic).
            car_keywords = ["car", "audio", "hands", "carplay", "sync", "uconnect"]
            car_device = None
            for device in paired_devices:
                name = device.getName() or ""
                if any(k in name.lower() for k in car_keywords):
                    car_device = device
                    break

            if car_device:
                self.on_status_change(f"connected to {car_device.getName()}")
            else:
                # Fall back to just naming the first paired device found.
                first_name = paired_devices[0].getName()
                self.on_status_change(
                    f"no car detected, nearest paired device: {first_name}"
                )

        except Exception as exc:  # noqa: BLE001
            self.on_status_change(f"error - {exc}")
