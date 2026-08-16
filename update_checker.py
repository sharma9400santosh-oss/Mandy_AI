"""
Update checker: looks at a GitHub repo's public Releases (read-only,
no authentication needed since it's your own public repo) to tell you
if a newer version of Mandy is available.

DELIBERATE DESIGN CHOICE: this never downloads or installs anything by
itself. It only tells you a new version exists and opens the release
page in your browser, where YOU choose to download and YOU tap to
install (Android requires that manual tap regardless -- there's no way
for an app to silently install another APK without you approving it in
that moment, and this doesn't try to work around that).

This intentionally avoids the pattern of "a server response silently
triggers an install prompt" -- that's a real sideloading risk if the
update-check endpoint is ever spoofed or compromised. A public, read-only
GitHub Releases page has no such risk: it's exactly as trustworthy as
your own GitHub account is.
"""

import json
import urllib.request
import urllib.error

from kivy.utils import platform


def check_latest_release(repo: str):
    """
    repo: "yourusername/yourrepo"
    Returns (latest_version: str|None, release_url: str|None, error: str|None)
    """
    if not repo:
        return None, None, "No GitHub repo configured in Settings"

    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        version = data.get("tag_name")
        url = data.get("html_url")
        return version, url, None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, None, "No releases published yet for this repo"
        return None, None, f"GitHub check failed: HTTP {exc.code}"
    except urllib.error.URLError:
        return None, None, "Couldn't reach GitHub -- check your internet connection"
    except Exception as exc:  # noqa: BLE001
        return None, None, f"Update check failed: {exc}"


def open_release_page(url: str):
    """Opens the release page in the browser -- download and install
    remain manual, user-driven steps from there."""
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
        print(f"Could not open release page: {exc}")
