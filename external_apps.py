"""
Launches official third-party apps Mandy can't integrate with directly
(no public API access for any of these) -- opens the real app if
installed, otherwise sends you to its Play Store listing.
"""

from kivy.utils import platform

# Play Store fallback links (used if the app isn't installed).
PLAY_STORE_LINKS = {
    "rajmargyatra": "https://play.google.com/store/apps/details?id=com.rajmarg.yatra",
    "mparivahan": "https://play.google.com/store/apps/details?id=org.tsat.mparivahan",
}

# Best-known package names (may change on the Play Store over time).
PACKAGE_NAMES = {
    "rajmargyatra": "com.rajmarg.yatra",
    "mparivahan": "org.tsat.mparivahan",
}


def _try_launch_package(package_name: str) -> bool:
    if platform != "android":
        print(f"[dev mode] Would launch package: {package_name}")
        return True
    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        activity = PythonActivity.mActivity

        intent = activity.getPackageManager().getLaunchIntentForPackage(package_name)
        if intent is None:
            return False
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Launch failed for {package_name}: {exc}")
        return False


def _open_play_store(url: str):
    if platform != "android":
        print(f"[dev mode] Would open Play Store: {url}")
        return
    try:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
    except Exception as exc:  # noqa: BLE001
        print(f"Play Store open failed: {exc}")


def open_rajmargyatra():
    if not _try_launch_package(PACKAGE_NAMES["rajmargyatra"]):
        _open_play_store(PLAY_STORE_LINKS["rajmargyatra"])


def open_mparivahan():
    if not _try_launch_package(PACKAGE_NAMES["mparivahan"]):
        _open_play_store(PLAY_STORE_LINKS["mparivahan"])


def open_insurer_app(package_name: str):
    """package_name comes from Settings -- every insurer has a different
    app, so there's no single default to launch."""
    if not package_name:
        print("No insurer app package name configured in Settings.")
        return False
    return _try_launch_package(package_name)
