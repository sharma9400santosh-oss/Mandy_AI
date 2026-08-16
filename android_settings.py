"""
Opens Android's system settings screen where the user can allow this
app to install other APKs (needed for the manual update-install flow).

IMPORTANT: Android does not allow any app to silently grant itself this
permission -- it's a deliberate security boundary (this exact permission
is what lets an app install other software, so Android requires an
explicit, visible user approval every time it's granted to a new app).
This function can only open the right settings screen; the actual
toggle still has to be tapped by the person using the phone.
"""

from kivy.utils import platform


def open_unknown_sources_settings():
    if platform != "android":
        print("[dev mode] Would open: install-unknown-apps settings screen")
        return

    try:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        Settings = autoclass("android.provider.Settings")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity

        package_name = activity.getPackageName()
        uri = Uri.parse(f"package:{package_name}")

        intent = Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, uri)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)

    except Exception as exc:  # noqa: BLE001
        print(f"Could not open unknown-sources settings: {exc}")
