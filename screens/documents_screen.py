"""
Documents screen: your vehicle number plus expiry dates for Insurance,
PUC, Registration, and Driving License, with color-coded status.

See vehicle_documents.py for the important scope note: these dates are
whatever you enter, not verified against any government database.
"""

from datetime import date, datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner

import vehicle_documents as docs
import external_apps

STATUS_COLORS = {
    "ok": (0.3, 0.8, 0.4, 1),
    "expiring_soon": (0.9, 0.7, 0.2, 1),
    "expired": (0.9, 0.3, 0.3, 1),
    "not_set": (0.6, 0.6, 0.6, 1),
}
STATUS_TEXT = {
    "ok": "Valid",
    "expiring_soon": "Expiring soon",
    "expired": "EXPIRED",
    "not_set": "Not set",
}


class DocumentsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_inputs = {}
        self._status_labels = {}

        outer = BoxLayout(orientation="vertical", padding=16, spacing=10)

        back_btn = Button(text="< Back", size_hint=(1, None), height=44, font_size="16sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        outer.add_widget(back_btn)

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None, padding=(0, 4))
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(Label(text="Vehicle & Documents", font_size="22sp",
                                  size_hint_y=None, height=36))
        content.add_widget(Label(
            text="Dates below are what you enter -- this isn't connected to any "
                 "government database, it just tracks what you tell it.",
            font_size="11sp", color=(0.65, 0.65, 0.65, 1),
            size_hint_y=None, height=34))

        content.add_widget(Label(text="Vehicle number", font_size="13sp",
                                  size_hint_y=None, height=26))
        self.vehicle_input = TextInput(text=docs.get_vehicle_number(),
                                        size_hint_y=None, height=44, multiline=False)
        content.add_widget(self.vehicle_input)

        content.add_widget(Label(text="Make", font_size="13sp",
                                  size_hint_y=None, height=26))
        self.make_spinner = Spinner(
            text=docs.get_vehicle_make() or "Other",
            values=docs.VEHICLE_MAKES,
            size_hint_y=None, height=44,
        )
        content.add_widget(self.make_spinner)

        content.add_widget(Label(text="Model", font_size="13sp",
                                  size_hint_y=None, height=26))
        self.model_input = TextInput(text=docs.get_vehicle_model(),
                                      hint_text="e.g. Nexon, Swift, Creta",
                                      size_hint_y=None, height=44, multiline=False)
        content.add_widget(self.model_input)

        for key in docs.DOC_KEYS:
            content.add_widget(self._build_doc_row(key))

        save_btn = Button(text="Save", font_size="18sp", size_hint_y=None, height=50,
                           background_color=(0.2, 0.6, 0.3, 1))
        save_btn.bind(on_press=self._save)
        content.add_widget(save_btn)

        self.status_label = Label(text="", font_size="13sp", size_hint_y=None, height=28)
        content.add_widget(self.status_label)

        content.add_widget(Label(text="Related apps (opens the real app -- Mandy can't "
                                       "read their data directly)",
                                  font_size="11sp", color=(0.65, 0.65, 0.65, 1),
                                  size_hint_y=None, height=34))

        apps_row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        rmy_btn = Button(text="RajmargYatra", background_color=(0.2, 0.5, 0.8, 1))
        rmy_btn.bind(on_press=lambda *_: external_apps.open_rajmargyatra())
        mpv_btn = Button(text="mParivahan", background_color=(0.3, 0.55, 0.3, 1))
        mpv_btn.bind(on_press=lambda *_: external_apps.open_mparivahan())
        ins_btn = Button(text="Insurance App", background_color=(0.6, 0.4, 0.2, 1))
        ins_btn.bind(on_press=self._open_insurer_app)
        apps_row.add_widget(rmy_btn)
        apps_row.add_widget(mpv_btn)
        apps_row.add_widget(ins_btn)
        content.add_widget(apps_row)

        scroll.add_widget(content)
        outer.add_widget(scroll)
        self.add_widget(outer)

    def _build_doc_row(self, key):
        row_container = BoxLayout(orientation="vertical", size_hint_y=None, height=90, spacing=4)

        header_row = BoxLayout(size_hint_y=None, height=26)
        header_row.add_widget(Label(text=docs.DOC_LABELS[key], font_size="14sp"))
        status_label = Label(text="", font_size="13sp", bold=True)
        header_row.add_widget(status_label)
        row_container.add_widget(header_row)

        existing = docs.get_document_date(key)
        date_input = TextInput(
            text=existing.strftime("%Y-%m-%d") if existing else "",
            hint_text="YYYY-MM-DD",
            size_hint_y=None, height=44, multiline=False,
        )
        row_container.add_widget(date_input)

        self.date_inputs[key] = date_input
        self._status_labels[key] = status_label
        self._refresh_status_label(key)

        return row_container

    def _refresh_status_label(self, key):
        status, days_left = docs.document_status(key)
        label = self._status_labels[key]
        if days_left is None:
            label.text = STATUS_TEXT[status]
        elif days_left >= 0:
            label.text = f"{STATUS_TEXT[status]} ({days_left}d)"
        else:
            label.text = f"{STATUS_TEXT[status]} ({abs(days_left)}d ago)"
        label.color = STATUS_COLORS[status]

    def _save(self, *_):
        docs.set_vehicle_number(self.vehicle_input.text)
        docs.set_vehicle_make(self.make_spinner.text)
        docs.set_vehicle_model(self.model_input.text)

        errors = []
        for key, input_widget in self.date_inputs.items():
            text = input_widget.text.strip()
            if not text:
                continue
            try:
                parsed = datetime.strptime(text, "%Y-%m-%d").date()
                docs.set_document_date(key, parsed)
            except ValueError:
                errors.append(docs.DOC_LABELS[key])

        for key in self.date_inputs:
            self._refresh_status_label(key)

        if errors:
            self.status_label.text = f"Couldn't parse date for: {', '.join(errors)} (use YYYY-MM-DD)"
        else:
            self.status_label.text = "Saved."

    def _open_insurer_app(self, *_):
        import settings_store as store

        package = store.get("insurer_app_package")
        if not package:
            self.status_label.text = "Set your insurer's app package name in Settings first."
            return
        external_apps.open_insurer_app(package)
