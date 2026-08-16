"""
obd_dtc.py — reads stored Diagnostic Trouble Codes (Mode 03) over the same
ELM327 Bluetooth connection OBDReader already opens for live PIDs.

Your current obd_reader.py polls RPM_PID / SPEED_PID / FUEL_LEVEL_PID /
AMBIENT_TEMP_PID (Mode 01) but has no Mode 03 (stored fault codes) support —
that's the piece behind "what's this light on my dashboard?" in the
MongoDB Leafy-style flow: a real code has to come off the vehicle before
Mandy can explain it.

This module doesn't touch obd_reader.py. It reuses the same
java Bluetooth socket object obd_reader already keeps on self._socket, so
integration is one call site:

    # inside obd_reader.py's OBDReader, after connect() succeeds:
    from obd_dtc import read_dtc_codes
    codes = read_dtc_codes(self._socket)   # -> ['P0301', 'P0133', ...]

If you'd rather not import across modules, copy `_send_and_read` and
`read_dtc_codes` directly into OBDReader as a method — the socket handling
matches the pattern already in your `_send_at`.
"""

# Minimal local fallback descriptions, used only if the LLM call fails or
# there's no network — Mandy should still say *something* useful offline.
# Anything not listed here still gets passed to the LLM with the raw code.
COMMON_DTC_HINTS = {
    "P0128": "Coolant is taking too long to reach operating temperature — often a stuck-open thermostat.",
    "P0133": "Oxygen sensor response is slower than expected — sensor may be aging.",
    "P0171": "Engine is running leaner than expected on one fuel bank — check for a vacuum leak.",
    "P0301": "Misfire detected on cylinder 1.",
    "P0302": "Misfire detected on cylinder 2.",
    "P0303": "Misfire detected on cylinder 3.",
    "P0304": "Misfire detected on cylinder 4.",
    "P0420": "Catalytic converter efficiency is below threshold.",
    "P0455": "Large EVAP system leak detected — often a loose or missing fuel cap.",
    "P0521": "Engine oil pressure sensor/switch reading is out of range.",
    "P0562": "System voltage is lower than expected — check the battery and charging system.",
    "C0051": "Brake fluid level sensor is reporting below minimum.",
    "B1318": "Battery voltage is low, possibly a weak alternator connection.",
}


def _decode_dtc_bytes(byte_pair):
    """Two raw bytes -> a code like 'P0301', per SAE J2012 encoding."""
    b1, b2 = byte_pair
    prefix_bits = (b1 & 0xC0) >> 6
    prefix = {0: "P", 1: "C", 2: "B", 3: "U"}[prefix_bits]
    digit1 = (b1 & 0x30) >> 4
    digit2 = b1 & 0x0F
    digit3 = (b2 & 0xF0) >> 4
    digit4 = b2 & 0x0F
    return f"{prefix}{digit1}{digit2:X}{digit3:X}{digit4:X}"


def _send_and_read(socket, command):
    """
    Matches obd_reader.py's proven _query_pid() pattern exactly (blocking
    byte-at-a-time read until the adapter sends -1 or the '>' prompt,
    0x3E) rather than polling inp.available(), since that's the pattern
    already tested working against real ELM327 hardware in this project.
    """
    out = socket.getOutputStream()
    out.write((command + "\r").encode())
    out.flush()

    inp = socket.getInputStream()
    buffer = bytearray()
    while True:
        b = inp.read()
        if b in (-1, 0x3E):
            break
        buffer.append(b)
    return bytes(buffer).decode(errors="ignore")


def read_dtc_codes(socket):
    """
    Requests stored fault codes (Mode 03) and returns a list like
    ['P0301', 'P0133']. Returns [] if the car reports no stored codes,
    and raises if the adapter/socket itself is unreachable (same failure
    mode as the rest of OBDReader, so callers should already be wrapping
    connect()-dependent calls in try/except).
    """
    raw = _send_and_read(socket, "03")

    hex_bytes = []
    for token in raw.replace("\r", " ").split():
        token = token.strip()
        if len(token) == 2 and all(c in "0123456789ABCDEFabcdef" for c in token):
            hex_bytes.append(int(token, 16))

    # Response starts with 0x43 (Mode 03 positive response). Skip it and
    # any immediate DTC-count byte some adapters prepend.
    if hex_bytes and hex_bytes[0] == 0x43:
        hex_bytes = hex_bytes[1:]

    codes = []
    for i in range(0, len(hex_bytes) - 1, 2):
        pair = (hex_bytes[i], hex_bytes[i + 1])
        if pair == (0, 0):
            continue
        codes.append(_decode_dtc_bytes(pair))

    return codes


def local_hint(code):
    return COMMON_DTC_HINTS.get(code.upper())
