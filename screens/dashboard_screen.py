"""
Dashboard screen: multifunction speedometer (real GPS speed), RPM gauge
(real, needs OBD-II adapter), fuel gauge + km/l estimate (real, needs
OBD-II adapter AND vehicle support), live trip distance (real, GPS-only),
live clock/date, toll plaza alerts, and speed-limit warnings.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import mainthread, Clock

from widgets import Gauge
from clock_widget import ClockWidget
from gps_speed import SpeedTracker
from obd_reader import OBDReader
from toll_engine import TollEngine
from speed_limit_tracker import SpeedLimitTracker
from trip_computer import TripComputer
import climate_alert
import settings_store as store

from warning_rail import WarningRail
from chat_panel import ChatPanel
from diagnostics_explainer import DiagnosticsExplainer
import obd_dtc


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.trip_computer = TripComputer()
        self.speed_tracker = SpeedTracker(
            on_speed_update=self._update_speed,
            on_location_update=self._on_location_update,
        )
        self.obd_reader = OBDReader(
            on_rpm_update=self._update_rpm,
            on_status_change=self._update_obd_status,
            on_fuel_update=self._on_fuel_update,
            on_temp_update=self._on_temp_update,
        )
        self.toll_engine = TollEngine(on_toll_approaching=self._on_toll_approaching)
        self.speed_limit_tracker = SpeedLimitTracker(
            on_limit_update=self._on_limit_update,
            on_over_limit=self._on_over_limit,
        )
        self._started = False
        self._last_speed = 0.0

        # Set up on first on_enter, once HomeScreen (and therefore the
        # shared avatar / conversation engine / tts) is guaranteed to
        # exist on the ScreenManager. See _ensure_diagnostics_wired().
        self.warning_rail = None
        self.chat_panel = None
        self.explainer = None
        self._diagnostics_wired = False

        root = BoxLayout(orientation="vertical", padding=16, spacing=8)

        top_row = BoxLayout(size_hint=(1, 0.1), spacing=8)
        back_btn = Button(text="< Back", font_size="16sp", size_hint=(0.3, 1))
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        top_row.add_widget(back_btn)
        self.clock_widget = ClockWidget(font_size="16sp", halign="right",
                                         size_hint=(0.7, 1))
        top_row.add_widget(self.clock_widget)
        root.add_widget(top_row)

        gauges_row = BoxLayout(size_hint=(1, 0.42), spacing=12)
        self.speed_gauge = Gauge(max_value=200, unit="km/h", accent=(0.2, 0.8, 0.5, 1))
        self.rpm_gauge = Gauge(max_value=8000, unit="RPM", accent=(0.9, 0.5, 0.2, 1))
        fuel_label = "Charge %" if store.get("fuel_type") == "Battery" else "Fuel %"
        self.fuel_gauge = Gauge(max_value=100, unit=fuel_label, accent=(0.3, 0.6, 0.9, 1))
        gauges_row.add_widget(self.speed_gauge)
        gauges_row.add_widget(self.rpm_gauge)
        gauges_row.add_widget(self.fuel_gauge)
        root.add_widget(gauges_row)

        self.obd_status_label = Label(
            text="RPM/Fuel: connect an OBD-II Bluetooth adapter for real data "
                 "(fuel level support varies by vehicle)",
            font_size="11sp", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.07),
        )
        root.add_widget(self.obd_status_label)

        trip_row = BoxLayout(size_hint=(1, 0.09), spacing=10)
        self.trip_label = Label(text="Trip: 0.0 km", font_size="15sp")
        trip_row.add_widget(self.trip_label)
        self.efficiency_label = Label(text="Efficiency: --", font_size="14sp",
                                       color=(0.7, 0.7, 0.7, 1))
        trip_row.add_widget(self.efficiency_label)
        reset_trip_btn = Button(text="Reset Trip", size_hint=(0.3, 1), font_size="12sp")
        reset_trip_btn.bind(on_press=self._reset_trip)
        trip_row.add_widget(reset_trip_btn)
        root.add_widget(trip_row)

        self.speed_limit_label = Label(
            text="Speed limit: --",
            font_size="14sp", color=(0.8, 0.8, 0.8, 1), size_hint=(1, 0.08),
        )
        root.add_widget(self.speed_limit_label)

        self.climate_label = Label(
            text="Outside temp: -- (needs OBD-II adapter)",
            font_size="13sp", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.08),
        )
        root.add_widget(self.climate_label)

        self.toll_banner = Label(
            text="No toll nearby",
            font_size="13sp", color=(0.6, 0.6, 0.6, 1), size_hint=(1, 0.08),
        )
        root.add_widget(self.toll_banner)

        # --- Warning-light rail + chat log ---
        # Fixed heights (size_hint_y=None) so they don't disturb the
        # proportional sizing of the rows above.
        diag_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                              height=200, spacing=10)

        self.warning_rail = WarningRail(
            on_icon_pressed=self._on_warning_pressed,
            size_hint=(None, 1), width=64,
        )
        diag_row.add_widget(self.warning_rail)

        # ChatPanel needs the shared avatar / conversation engine / tts,
        # which live on HomeScreen. Built as a placeholder here and
        # actually constructed in _ensure_diagnostics_wired() the first
        # time this screen is entered, once self.manager is available.
        self._chat_slot = BoxLayout(orientation="vertical", size_hint=(1, 1))
        diag_row.add_widget(self._chat_slot)

        root.add_widget(diag_row)

        self.add_widget(root)

    def _ensure_diagnostics_wired(self):
        if self._diagnostics_wired:
            return
        self._diagnostics_wired = True

        home = self.manager.get_screen("home")

        self.chat_panel = ChatPanel(
            conversation_engine=home.conversation,
            avatar=home.avatar,
            tts=home.tts,
            screen_manager=self.manager,
        )
        self._chat_slot.add_widget(self.chat_panel)

        self.explainer = DiagnosticsExplainer(
            llm_client=home.conversation.llm_client,
            avatar=home.avatar,
            tts=home.tts,
            on_result=self.chat_panel.add_mandy_message,
        )

    def _on_warning_pressed(self, key):
        if not self._diagnostics_wired:
            self._ensure_diagnostics_wired()

        if not self.obd_reader._socket:
            self.chat_panel.add_mandy_message(
                "I can't run a live diagnostic without an OBD-II adapter "
                "connected -- pair your ELM327 dongle first."
            )
            return

        self.explainer.explain(
            self.obd_reader._socket, user_name=store.get("user_name")
        )

    def on_enter(self, *_):
        if not self._started:
            self.speed_tracker.start()
            self.obd_reader.connect()
            self._started = True
            # Periodic background check for stored fault codes, so a
            # warning light gets explained even if it's never tapped.
            # NOTE: generic OBD-II Mode 03 codes can't be reliably mapped
            # to *which specific* icon (oil vs. tire vs. brake vs.
            # battery) caused them -- tire pressure and brake fluid
            # aren't standard OBD PIDs at all. Being honest about that:
            # this lights every icon together as "something needs
            # attention" rather than pretending to pinpoint one.
            Clock.schedule_interval(self._background_dtc_check, 90)
        self._ensure_diagnostics_wired()
        self.trip_label.text = f"Trip: {self.trip_computer.get_trip_km():.1f} km"

    def _background_dtc_check(self, dt):
        if not self.obd_reader._socket:
            return
        import threading
        threading.Thread(target=self._background_dtc_worker, daemon=True).start()

    def _background_dtc_worker(self):
        try:
            codes = obd_dtc.read_dtc_codes(self.obd_reader._socket)
        except Exception:
            return
        if codes:
            Clock.schedule_once(lambda dt: self._set_all_warning_faults(True), 0)

    def _set_all_warning_faults(self, is_fault):
        if self.warning_rail:
            for key in ("oil", "tire", "battery", "brake"):
                self.warning_rail.set_fault(key, is_fault)

    def _reset_trip(self, *_):
        self.trip_computer.reset_trip()
        self.trip_label.text = "Trip: 0.0 km"
        self.efficiency_label.text = "Efficiency: --"

    @mainthread
    def _update_speed(self, speed_kmh):
        self._last_speed = speed_kmh
        self.speed_gauge.set_value(speed_kmh)

    @mainthread
    def _update_rpm(self, rpm):
        self.rpm_gauge.set_value(rpm)

    @mainthread
    def _update_obd_status(self, status_text):
        self.obd_status_label.text = f"OBD: {status_text}"

    @mainthread
    def _on_fuel_update(self, fuel_pct):
        self.fuel_gauge.set_value(fuel_pct)
        self.trip_computer.update_fuel_level(fuel_pct)
        km_per_l = self.trip_computer.get_estimated_km_per_litre()
        if km_per_l:
            self.efficiency_label.text = f"Efficiency: ~{km_per_l} km/l"
        else:
            self.efficiency_label.text = "Efficiency: gathering data..."

    @mainthread
    def _on_temp_update(self, temp_c):
        alert = climate_alert.check_temperature(temp_c)
        if alert and store.get("climate_alerts_enabled"):
            self.climate_label.text = alert
            self.climate_label.color = (0.95, 0.7, 0.3, 1)
        else:
            self.climate_label.text = f"Outside temp: {temp_c:.0f}°C"
            self.climate_label.color = (0.7, 0.7, 0.7, 1)

    def _on_location_update(self, lat, lon, speed_kmh):
        self.toll_engine.update_location(lat, lon)
        self.speed_limit_tracker.update(lat, lon, speed_kmh)
        self.trip_computer.update_location(lat, lon)
        Clock.schedule_once(lambda dt: self._refresh_trip_label(), 0)

    @mainthread
    def _refresh_trip_label(self):
        self.trip_label.text = f"Trip: {self.trip_computer.get_trip_km():.1f} km"

    @mainthread
    def _on_toll_approaching(self, name, price, vehicle_class):
        if price is not None:
            self.toll_banner.text = f"Toll ahead: {name} -- approx Rs {price} ({vehicle_class})"
        else:
            self.toll_banner.text = f"Toll ahead: {name} -- price not set in database"
        self.toll_banner.color = (0.95, 0.75, 0.25, 1)
        Clock.schedule_once(lambda dt: self._reset_toll_banner(), 15)

    def _reset_toll_banner(self):
        self.toll_banner.text = "No toll nearby"
        self.toll_banner.color = (0.6, 0.6, 0.6, 1)

    @mainthread
    def _on_limit_update(self, limit_kmh):
        if limit_kmh:
            self.speed_limit_label.text = f"Speed limit: {limit_kmh} km/h"
            self.speed_limit_label.color = (0.8, 0.8, 0.8, 1)
        else:
            self.speed_limit_label.text = "Speed limit: not tagged for this road"
            self.speed_limit_label.color = (0.6, 0.6, 0.6, 1)

    @mainthread
    def _on_over_limit(self, current_kmh, limit_kmh):
        self.speed_limit_label.text = (
            f"Over limit! {current_kmh:.0f} km/h in a {limit_kmh} km/h zone"
        )
        self.speed_limit_label.color = (0.95, 0.3, 0.3, 1)
