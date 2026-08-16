"""
Mandy's voice output.

Honest limitation: Android's built-in TextToSpeech engine does not support
true emotional prosody (no "sound sad" parameter). What we *can* control
is speech rate and pitch, which we adjust based on the detected emotion
to approximate tone -- e.g. slower + lower pitch for a calm/supportive
reply, faster + slightly higher for urgency/excitement. It reads more
"expressive" than flat, but it isn't studio-actor-level emotional speech.
For that, you'd eventually want a cloud TTS with emotion tags (e.g.
ElevenLabs, Azure Neural TTS styles) -- swap-in point is noted below.
"""

from kivy.utils import platform

EMOTION_VOICE_PARAMS = {
    "neutral":    {"pitch": 1.0, "rate": 1.0},
    "calm":       {"pitch": 0.92, "rate": 0.88},
    "supportive": {"pitch": 0.95, "rate": 0.9},
    "urgent":     {"pitch": 1.08, "rate": 1.15},
    "happy":      {"pitch": 1.1, "rate": 1.05},
    "concerned":  {"pitch": 0.9, "rate": 0.85},
}


class TTSEngine:
    def __init__(self):
        self._android_tts = None
        if platform == "android":
            self._init_android_tts()

    def _init_android_tts(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method

            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            class InitListener(PythonJavaClass):
                __javainterfaces__ = [
                    "android/speech/tts/TextToSpeech$OnInitListener"
                ]
                __javacontext__ = "app"

                def __init__(self, outer):
                    super().__init__()
                    self.outer = outer

                @java_method("(I)V")
                def onInit(self, status):
                    pass  # ready

            self._init_listener = InitListener(self)
            self._android_tts = TextToSpeech(activity, self._init_listener)
        except Exception as exc:  # noqa: BLE001
            print(f"TTS init failed: {exc}")
            self._android_tts = None

    def speak(self, text: str, emotion: str = "neutral"):
        params = EMOTION_VOICE_PARAMS.get(emotion, EMOTION_VOICE_PARAMS["neutral"])

        if platform == "android" and self._android_tts is not None:
            try:
                from jnius import autoclass

                TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
                self._android_tts.setPitch(params["pitch"])
                self._android_tts.setSpeechRate(params["rate"])
                self._android_tts.speak(
                    text, TextToSpeech.QUEUE_FLUSH, None, "mandy_utterance"
                )
            except Exception as exc:  # noqa: BLE001
                print(f"TTS speak failed: {exc}")
        else:
            # Desktop dev fallback -- just print what she'd say.
            print(f"[Mandy ({emotion})]: {text}")
            try:
                import pyttsx3

                engine = pyttsx3.init()
                engine.setProperty("rate", int(180 * params["rate"]))
                engine.say(text)
                engine.runAndWait()
            except ImportError:
                pass

    # ---- Swap-in point for a cloud emotional TTS (ElevenLabs/Azure/etc) ----
    # def speak_cloud(self, text, emotion):
    #     audio_bytes = call_your_tts_api(text=text, style=emotion)
    #     play(audio_bytes)
