"""
Media manager: launches YouTube, Spotify, and internet radio streams.

Honest scope: these hand off to the real apps (or a stream URL) rather
than reimplementing music/video playback -- that's the standard,
reliable way to do this without needing YouTube/Spotify API credentials
and OAuth flows for a personal project. Deep in-app control (e.g.
"skip track" without opening Spotify) would need the Spotify Web API
with your own app registration -- doable as a later phase.
"""

from urllib.parse import quote
from kivy.utils import platform

# A few example internet radio streams -- replace/add your own.
RADIO_STATIONS = {
    "default": "http://stream.radioparadise.com/aac-320",
    "news": "http://stream.radioparadise.com/mellow-320",
}


def _launch_intent(package, uri=None, view_action=True):
    try:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity

        if uri:
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(uri))
        else:
            intent = activity.getPackageManager().getLaunchIntentForPackage(package)

        if intent is None:
            return False

        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Launch intent failed: {exc}")
        return False


def open_spotify(query: str = ""):
    if platform != "android":
        print(f"[dev mode] Would open Spotify search: {query}")
        return

    if query:
        uri = f"spotify:search:{quote(query)}"
        if _launch_intent("com.spotify.music", uri=uri):
            return
    # Fall back to just opening the app.
    _launch_intent("com.spotify.music")


def open_youtube(query: str = ""):
    if platform != "android":
        print(f"[dev mode] Would open YouTube search: {query}")
        return

    if query:
        uri = f"https://www.youtube.com/results?search_query={quote(query)}"
        _launch_intent(None, uri=uri)
    else:
        _launch_intent("com.google.android.youtube")


def open_radio(station_key: str = "default"):
    stream_url = RADIO_STATIONS.get(station_key, RADIO_STATIONS["default"])

    if platform != "android":
        print(f"[dev mode] Would stream radio: {stream_url}")
        return

    # Hand off to whatever the phone uses for audio streams (browser/player).
    _launch_intent(None, uri=stream_url)
