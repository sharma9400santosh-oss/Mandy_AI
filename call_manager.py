"""
Call manager: places phone calls by name (looked up from contacts) or
number, using Android's native dialer.

Note: directly placing a call (vs. just opening the dialer pre-filled)
requires the CALL_PHONE permission, which Google treats as sensitive
and scrutinizes for Play Store apps. Since this is a personal/sideloaded
app, that's not a blocker -- but worth knowing if you ever publish it.
"""

from kivy.utils import platform


def call_contact(name_or_number: str):
    if platform != "android":
        print(f"[dev mode] Would call: {name_or_number}")
        return "dev mode - no real call placed"

    try:
        from jnius import autoclass
        from android.permissions import request_permissions, Permission

        request_permissions([Permission.CALL_PHONE, Permission.READ_CONTACTS])

        number = _resolve_contact_number(name_or_number)
        if not number:
            return f"Couldn't find a contact named {name_or_number}"

        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_CALL, Uri.parse(f"tel:{number}"))
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
        return f"Calling {name_or_number}"

    except Exception as exc:  # noqa: BLE001
        return f"Call failed: {exc}"


def _resolve_contact_number(name_or_number: str):
    """If it's already a phone number, use it directly. Otherwise look it
    up in the phone's contacts by display name (first match)."""
    digits = "".join(ch for ch in name_or_number if ch.isdigit() or ch == "+")
    if len(digits) >= 7:
        return digits

    try:
        from jnius import autoclass, cast

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ContactsContract = autoclass("android.provider.ContactsContract$Contacts")
        CommonDataKinds = autoclass(
            "android.provider.ContactsContract$CommonDataKinds$Phone"
        )
        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()

        cursor = resolver.query(
            CommonDataKinds.CONTENT_URI, None, None, None, None
        )
        if cursor is None:
            return None

        name_idx = cursor.getColumnIndex(CommonDataKinds.DISPLAY_NAME)
        number_idx = cursor.getColumnIndex(CommonDataKinds.NUMBER)

        target = name_or_number.strip().lower()
        while cursor.moveToNext():
            contact_name = cursor.getString(name_idx) or ""
            if target in contact_name.lower():
                number = cursor.getString(number_idx)
                cursor.close()
                return number

        cursor.close()
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"Contact lookup failed: {exc}")
        return None
