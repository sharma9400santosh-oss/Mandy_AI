"""
Mandy - Voice-controlled car AI assistant
Main application entry point (Kivy)

Screens:
  Home       - Mandy's face, voice interaction, quick nav
  Dashboard  - Speedometer + RPM gauges
  Media      - Spotify / YouTube / Radio
  Calls      - Phone calling
  Navigate   - Manual destination entry (voice also works from Home)
  Settings   - Name, wake phrase, voice personality, AI backend key
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.utils import platform

from screens.home_screen import HomeScreen
from screens.dashboard_screen import DashboardScreen
from screens.media_screen import MediaScreen
from screens.calls_screen import CallsScreen
from screens.navigate_screen import NavigateScreen
from screens.settings_screen import SettingsScreen
from screens.documents_screen import DocumentsScreen
from screens.file_explorer_screen import FileExplorerScreen
from screens.connectivity_screen import ConnectivityScreen
from screens.onboarding_screen import OnboardingScreen
from screens.camera_screen import CameraScreen
from screens.app_drawer_screen import AppDrawerScreen
from screens.advanced_mode_screen import AdvancedModeScreen
import settings_store as store

Window.clearcolor = (0.05, 0.05, 0.08, 1)


class MandyApp(App):
    def build(self):
        self._set_landscape()

        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(OnboardingScreen(name="onboarding"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(MediaScreen(name="media"))
        sm.add_widget(CallsScreen(name="calls"))
        sm.add_widget(NavigateScreen(name="navigate"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(DocumentsScreen(name="documents"))
        sm.add_widget(FileExplorerScreen(name="files"))
        sm.add_widget(ConnectivityScreen(name="connectivity"))
        sm.add_widget(CameraScreen(name="camera"))
        sm.add_widget(AppDrawerScreen(name="apps"))
        sm.add_widget(AdvancedModeScreen(name="advanced"))

        # Skip straight to Home if onboarding was already completed
        # (e.g. on every launch after the first).
        if store.get("onboarding_complete"):
            sm.current = "home"
        else:
            sm.current = "onboarding"

        return sm

    def _set_landscape(self):
        if platform == "android":
            try:
                from jnius import autoclass

                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                activity = PythonActivity.mActivity
                ActivityInfo = autoclass("android.content.pm.ActivityInfo")
                activity.setRequestedOrientation(
                    ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
                )
            except Exception:
                pass


if __name__ == "__main__":
    MandyApp().run()
