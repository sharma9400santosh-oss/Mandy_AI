"""
Launches third-party apps by package name (if installed) or falls back
to Play Store.

Two tiers, and it matters which one an app is in:

VERIFIED_APPS: package names I'm reasonably confident are current and
correct. These launch the app directly if installed, or open its exact
Play Store listing if not.

SEARCH_ONLY_APPS: apps where I don't have a verified, current package
name (these change, get renamed, or I simply don't have reliable data
for a regional/niche app). Rather than guess and silently fail, these
route through a Play Store SEARCH query instead of a direct link --
slightly less convenient (you pick the right result yourself) but
never wrong.

NOT INCLUDED: Siri. It's Apple/iOS-exclusive software -- there is no
Siri app for Android, and no way to make one exist here.
"""

from urllib.parse import quote
from kivy.utils import platform

VERIFIED_APPS = {
    "spotify": "com.spotify.music",
    "youtube_music": "com.google.android.apps.youtube.music",
    "youtube": "com.google.android.youtube",
    "whatsapp": "com.whatsapp",
    "waze": "com.waze",
    "google_assistant": "com.google.android.googlequicksearchbox",
    "alexa": "com.amazon.dee.app",
    "play_store": "com.android.vending",
    "google_maps": "com.google.android.apps.maps",
    "gmail": "com.google.android.gm",
    "google_calendar": "com.google.android.calendar",
    "phonepe": "com.phonepe.app",
    "gpay": "com.google.android.apps.nbu.paisa.user",
    "gaana": "com.gaana",
    "jiosaavn": "com.jio.media.jiobeats",
    "amazon_music": "com.amazon.mp3",
    "rajmargyatra": "com.rajmarg.yatra",
    "mparivahan": "org.tsat.mparivahan",
}

# App name shown to the user -> Play Store search query. Used for apps
# where the exact package name isn't reliably known to me.
SEARCH_ONLY_APPS = {
    "here_wego": "HERE WeGo",
    "mapmyindia": "MapMyIndia Move",
    "park_plus": "Park+",
    "indianoil": "IndianOil ONE",
    "hpcl": "HPCL fuel app",
    "bpcl": "BPCL Petro Card",
    "autoboy_dashcam": "AutoBoy Dashcam",
    "nexar_dashcam": "Nexar Dashcam",
    "tata_punch_connect": "Tata Motors Connect app",
    "bing_copilot": "Microsoft Copilot",
    "weather": "weather forecast app",
    "tpms": "TPMS tyre pressure monitor",
    "first_aid": "first aid guide",
}


def _launch_package(package_name: str) -> bool:
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


def _open_url(url: str):
    if platform != "android":
        print(f"[dev mode] Would open: {url}")
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
        print(f"Open URL failed: {exc}")


def open_app(app_key: str):
    """Launch a verified app by its key, falling back to its exact
    Play Store page if not installed."""
    package = VERIFIED_APPS.get(app_key)
    if not package:
        return False
    if not _launch_package(package):
        _open_url(f"https://play.google.com/store/apps/details?id={package}")
    return True


def search_play_store(app_key: str):
    """For apps without a verified package -- opens a Play Store search
    so the user picks the correct, current listing themselves."""
    query = SEARCH_ONLY_APPS.get(app_key)
    if not query:
        return False
    _open_url(f"market://search?q={quote(query)}")
    return True


def open_dialer():
    if platform != "android":
        print("[dev mode] Would open dialer")
        return
    try:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_DIAL)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
    except Exception as exc:  # noqa: BLE001
        print(f"Open dialer failed: {exc}")
