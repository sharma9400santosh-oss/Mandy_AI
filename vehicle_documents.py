"""
Vehicle & document tracker.

IMPORTANT SCOPE NOTE: this stores dates YOU enter and tells you when
they're expiring or expired. It does NOT verify anything against the
government's actual records (Vahan/Sarathi/mParivahan) -- there is no
public API for a third-party app to check that, so if you enter a wrong
date, this will confidently tell you the wrong thing. Treat it as a
personal reminder system, not an authority.
"""

import json
from datetime import date, datetime

import settings_store as store

DOC_KEYS = ["insurance", "puc", "registration", "driving_license"]
DOC_LABELS = {
    "insurance": "Insurance",
    "puc": "PUC (Pollution Under Control)",
    "registration": "Registration (RC)",
    "driving_license": "Driving License",
}

WARNING_WINDOW_DAYS = 30

# Common vehicle makes sold in India -- purely informational metadata
# for your profile/documents; does NOT unlock any special OBD access
# (see the note in obd_reader.py -- brand-specific data isn't available
# through the standard protocol regardless of what's selected here).
VEHICLE_MAKES = [
    "Maruti Suzuki", "Tata", "Hyundai", "Mahindra", "Honda", "Toyota",
    "Kia", "Renault", "Nissan", "Skoda", "Volkswagen", "MG", "Ford",
    "Other",
]


def get_vehicle_make():
    return store.get("vehicle_make")


def set_vehicle_make(make: str):
    store.set("vehicle_make", make)


def get_vehicle_model():
    return store.get("vehicle_model")


def set_vehicle_model(model: str):
    store.set("vehicle_model", model.strip())



def get_vehicle_number():
    return store.get("vehicle_number")


def set_vehicle_number(number: str):
    store.set("vehicle_number", number.strip().upper())


def get_document_date(doc_key: str):
    """Returns a date object or None if not set."""
    raw = store.get(f"doc_{doc_key}_expiry")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def set_document_date(doc_key: str, expiry_date: date):
    store.set(f"doc_{doc_key}_expiry", expiry_date.strftime("%Y-%m-%d"))


def document_status(doc_key: str):
    """Returns (status: 'ok'|'expiring_soon'|'expired'|'not_set', days_left: int|None)."""
    expiry = get_document_date(doc_key)
    if expiry is None:
        return "not_set", None

    days_left = (expiry - date.today()).days
    if days_left < 0:
        return "expired", days_left
    if days_left <= WARNING_WINDOW_DAYS:
        return "expiring_soon", days_left
    return "ok", days_left


def all_statuses():
    return {key: document_status(key) for key in DOC_KEYS}


def any_urgent():
    """True if anything is expired or expiring soon -- used for a home-screen banner."""
    for key in DOC_KEYS:
        status, _ = document_status(key)
        if status in ("expired", "expiring_soon"):
            return True
    return False
