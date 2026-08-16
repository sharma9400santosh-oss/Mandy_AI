# Changelog — v0.1 → v0.2

## New files
- `obd_dtc.py` — Mode 03 (stored fault code) reading. Reuses the same
  Bluetooth socket `obd_reader.py` already opens; read loop matches
  `obd_reader.py`'s proven `_query_pid()` pattern exactly (blocking
  byte read until `-1` or the `>` prompt), not a different approach.
- `warning_rail.py` — the oil/tire/battery/brake icon rail widget.
- `chat_panel.py` — on-screen chat log widget, drives off
  `ConversationEngine.process()`'s real return shape
  (`response_text` / `emotion` / `action` / `payload`).
- `diagnostics_explainer.py` — glue: DTC codes → `ClaudeMandyClient.reply()`
  → avatar state change → chat panel message.
- `screens/advanced_mode_screen.py` — raw settings_store editor.
- `assets/icon_warn_oil.png`, `icon_warn_tire.png`, `icon_warn_battery.png`,
  `icon_warn_brake.png` — generated for this update; no warning icons
  existed before.

## Modified files
- `main.py` — imports and registers `AdvancedModeScreen` (name="advanced").
- `screens/settings_screen.py` — added an "Advanced mode" button next to
  Save, navigates to the new screen. Nothing else in this file touched.
- `screens/dashboard_screen.py` — the real integration work:
  - imports `WarningRail`, `ChatPanel`, `DiagnosticsExplainer`, `obd_dtc`
  - adds a fixed-height row (`diag_row`, 200px) below the existing toll
    banner, containing the warning rail + a slot for the chat panel.
    Fixed height so it doesn't disturb the existing gauges/trip/speed
    rows' proportional sizing.
  - `_ensure_diagnostics_wired()`: lazily builds the `ChatPanel` and
    `DiagnosticsExplainer` on first `on_enter`, pulling
    `self.manager.get_screen("home").avatar` / `.conversation` / `.tts`
    — reuses HomeScreen's real instances rather than creating
    duplicates. Safe because all screens are constructed in `main.py`'s
    `build()` before any screen is shown, so `get_screen("home")` is
    guaranteed to resolve.
  - `_on_warning_pressed(key)`: guards against no adapter connected
    (`self.obd_reader._socket` falsy) with an honest message instead of
    a silent failure or fake data.
  - `_background_dtc_check` / `_background_dtc_worker`: polls for
    stored codes every 90s once OBD is connected, off the UI thread.
- `buildozer.spec` — version bumped 0.1 → 0.2. No other build config
  changed (permissions, archs, API levels all untouched).

## Verified before hand-off
- `python3 -m py_compile` on every `.py` file in the project: clean.
- A full headless run of the actual `main.py` / `MandyApp`, navigating
  through all 13 screens (including the new `advanced` one) with no
  exceptions, then exercising the new wiring specifically:
  `dashboard.warning_rail`, `dashboard.chat_panel`, and
  `dashboard.explainer` all construct correctly against the real
  `HomeScreen` instance; `warning_rail.set_fault()`,
  `chat_panel.add_mandy_message()`, `avatar.set_state()`, and
  `advanced_mode_screen._refresh_values()` all run without error.

## NOT verified (can't be, in this environment)
- `obd_dtc.py` against real ELM327 hardware — no device/adapter
  available here. The byte-parsing follows the SAE J2012 encoding
  correctly and mirrors your tested `_query_pid()` I/O pattern, but
  "correct per spec" and "handles your specific adapter's quirks" are
  different claims. Test this one first, expect a debugging pass.
- Actual Android build/install — this environment has no Android
  SDK/NDK access. See "Building the APK" below.
