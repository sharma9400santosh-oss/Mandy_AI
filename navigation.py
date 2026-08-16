"""
Navigation module.

Parses a spoken command like:
    "navigate to Pune railway station"
    "take me to the nearest petrol pump"
    "directions to Mandy's office"

...into a destination string, then launches Google Maps for
turn-by-turn navigation. No API key needed -- this uses Android's
geo intent, which hands off to whichever maps app the user has
installed (Google Maps by default).
"""

import re
import webbrowser
from urllib.parse import quote

from kivy.utils import platform

TRIGGER_PHRASES = [
    r"navigate to (.+)",
    r"take me to (.+)",
    r"directions to (.+)",
    r"drive to (.+)",
    r"go to (.+)",
    r"find (.+)",
]


def extract_destination(spoken_text: str):
    """Pull the destination out of a spoken sentence. Returns None if no
    recognizable navigation phrase was found."""
    text = spoken_text.strip().lower()

    for pattern in TRIGGER_PHRASES:
        match = re.search(pattern, text)
        if match:
            destination = match.group(1).strip()
            return destination

    # If no trigger phrase matched but the sentence is short, assume the
    # whole thing is the destination (e.g. user just said a place name).
    if 0 < len(text.split()) <= 6:
        return text

    return None


def launch_navigation(destination: str):
    """Launch turn-by-turn navigation to the given destination."""
    encoded = quote(destination)

    if platform == "android":
        _launch_android_maps(encoded)
    else:
        # Desktop/dev fallback: open in default web browser.
        webbrowser.open(f"https://www.google.com/maps/dir/?api=1&destination={encoded}")


def _launch_android_maps(encoded_destination: str):
    try:
        from jnius import autoclass, cast

        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        activity = PythonActivity.mActivity

        # google.navigation:q=<dest> triggers turn-by-turn directly in
        # Google Maps (falls back to any app that handles geo: intents).
        uri = Uri.parse(f"google.navigation:q={encoded_destination}&mode=d")
        intent = Intent(Intent.ACTION_VIEW, uri)
        intent.setPackage("com.google.android.apps.maps")
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

        try:
            activity.startActivity(intent)
        except Exception:
            # Google Maps not installed / package not found -- fall back
            # to a generic geo intent so any maps app can handle it.
            geo_uri = Uri.parse(f"geo:0,0?q={encoded_destination}")
            fallback_intent = Intent(Intent.ACTION_VIEW, geo_uri)
            fallback_intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(fallback_intent)

    except Exception as exc:  # noqa: BLE001
        print(f"Navigation launch failed: {exc}")
