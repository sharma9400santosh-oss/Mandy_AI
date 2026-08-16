"""
Wi-Fi status: whether Wi-Fi is on and which network you're connected to.
Read-only status check, no connecting/disconnecting (that's a system
settings action Android reserves for the user, by design, since Android 10).
"""

from kivy.utils import platform


def get_wifi_status():
    """Returns a human-readable status string."""
    if platform != "android":
        return "Wi-Fi status only available on Android device"

    try:
        from jnius import autoclass
        from android.permissions import request_permissions, Permission

        request_permissions(
            [Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_WIFI_STATE]
        )

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        activity = PythonActivity.mActivity

        wifi_manager = activity.getSystemService(Context.WIFI_SERVICE)

        if not wifi_manager.isWifiEnabled():
            return "Wi-Fi is off"

        wifi_info = wifi_manager.getConnectionInfo()
        ssid = wifi_info.getSSID() if wifi_info else None

        if not ssid or ssid == "<unknown ssid>":
            return "Wi-Fi on, not connected to a network"

        return f"Connected to {ssid.strip(chr(34))}"

    except Exception as exc:  # noqa: BLE001
        return f"Couldn't read Wi-Fi status: {exc}"
