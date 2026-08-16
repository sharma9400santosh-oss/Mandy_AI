"""
File explorer screen: browse the phone's storage. Read-only listing +
open a file with whatever app the phone associates with its type (tap
to open, like a normal file manager).
"""

import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform


def _default_root():
    if platform == "android":
        try:
            from android.storage import primary_external_storage_path

            return primary_external_storage_path()
        except Exception:
            return "/sdcard"
    return os.path.expanduser("~")


class FileExplorerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_path = _default_root()

        root = BoxLayout(orientation="vertical", padding=16, spacing=10)

        top_row = BoxLayout(size_hint=(1, 0.08), spacing=8)
        back_btn = Button(text="< Home", font_size="14sp")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        up_btn = Button(text="^ Up", font_size="14sp")
        up_btn.bind(on_press=self._go_up)
        top_row.add_widget(back_btn)
        top_row.add_widget(up_btn)
        root.add_widget(top_row)

        self.path_label = Label(text=self.current_path, font_size="12sp",
                                 size_hint=(1, 0.06), color=(0.7, 0.7, 0.7, 1))
        root.add_widget(self.path_label)

        self.scroll = ScrollView(size_hint=(1, 0.86))
        self.list_layout = BoxLayout(orientation="vertical", spacing=4,
                                      size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def on_enter(self, *_):
        self._refresh_listing()

    def _go_up(self, *_):
        parent = os.path.dirname(self.current_path.rstrip("/"))
        if parent:
            self.current_path = parent
            self._refresh_listing()

    def _refresh_listing(self):
        self.path_label.text = self.current_path
        self.list_layout.clear_widgets()

        try:
            entries = sorted(os.listdir(self.current_path))
        except Exception as exc:  # noqa: BLE001
            self.list_layout.add_widget(
                Label(text=f"Can't read this folder: {exc}",
                      size_hint_y=None, height=40)
            )
            return

        for entry in entries:
            full_path = os.path.join(self.current_path, entry)
            is_dir = os.path.isdir(full_path)
            label = f"[DIR]  {entry}" if is_dir else entry

            btn = Button(text=label, size_hint_y=None, height=44,
                         font_size="14sp", halign="left")
            btn.bind(on_press=lambda inst, p=full_path, d=is_dir: self._on_entry_press(p, d))
            self.list_layout.add_widget(btn)

    def _on_entry_press(self, path, is_dir):
        if is_dir:
            self.current_path = path
            self._refresh_listing()
        else:
            self._open_file(path)

    def _open_file(self, path):
        if platform != "android":
            print(f"[dev mode] Would open file: {path}")
            return
        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            uri = Uri.parse(f"file://{path}")
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, "*/*")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(intent)
        except Exception as exc:  # noqa: BLE001
            print(f"Could not open file: {exc}")
