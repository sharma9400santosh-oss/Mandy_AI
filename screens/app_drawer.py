"""
App drawer: lists every launchable app actually installed on the
device, straight from Android's own PackageManager. This is what
covers apps I have no way of reliably knowing the exact package name
for (TPMS apps, dashcam apps, regional fuel apps, etc.) -- if it's on
the phone, it shows up here correctly, no guessing involved.
"""

from kivy.utils import platform


def list_installed_apps():
    """Returns a list of {"label": str, "package": str} for every app
    with a launcher icon, sorted alphabetically by label."""
    if platform != "android":
        # Dev-mode placeholder list so the UI can be built/tested on desktop.
        return [
            {"label": "Example App One", "package": "com.example.one"},
            {"label": "Example App Two", "package": "com.example.two"},
        ]

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        activity = PythonActivity.mActivity
        pm = activity.getPackageManager()

        intent = Intent(Intent.ACTION_MAIN)
        intent.addCategory(Intent.CATEGORY_LAUNCHER)

        resolve_infos = pm.queryIntentActivities(intent, 0)
        apps = []
        for i in range(resolve_infos.size()):
            info = resolve_infos.get(i)
            try:
                label = str(info.loadLabel(pm))
                package = info.activityInfo.packageName
                apps.append({"label": label, "package": package})
            except Exception:
                continue

        # De-duplicate (some packages have multiple launcher activities)
        # and sort alphabetically.
        seen = set()
        unique_apps = []
        for app in sorted(apps, key=lambda a: a["label"].lower()):
            if app["package"] not in seen:
                seen.add(app["package"])
                unique_apps.append(app)

        return unique_apps

    except Exception as exc:  # noqa: BLE001
        print(f"Could not list installed apps: {exc}")
        return []


def launch_by_package(package_name: str) -> bool:
    if platform != "android":
        print(f"[dev mode] Would launch: {package_name}")
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
        print(f"Launch failed: {exc}")
        return False
