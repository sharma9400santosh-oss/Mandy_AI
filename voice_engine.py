"""
Voice engine: converts spoken audio to text, and captures the raw audio
alongside it so a voiceprint check can confirm *who* said it.

- On Android: uses the native Android SpeechRecognizer via pyjnius
  (fast, works offline for many languages, no API key needed). Raw
  16-bit PCM audio is captured via onBufferReceived as it streams in.
- On desktop (for testing without a phone): falls back to the
  `speech_recognition` package + Google's free web API, if installed.
"""

from kivy.utils import platform


class VoiceEngine:
    def __init__(self, on_result, on_error, on_listening_started=None):
        """
        on_result(text: str, raw_audio: bytes) is called with the
        recognized text AND the raw PCM16 audio for that utterance, so
        callers can run voiceprint verification if they want to.
        """
        self.on_result = on_result
        self.on_error = on_error
        self.on_listening_started = on_listening_started
        self._audio_buffer = bytearray()

    def listen_once(self):
        self._audio_buffer = bytearray()
        if self.on_listening_started:
            self.on_listening_started()

        if platform == "android":
            self._listen_android()
        else:
            self._listen_desktop()

    # ---------------- Android ----------------

    def _listen_android(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.RECORD_AUDIO])

            SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Locale = autoclass("java.util.Locale")

            activity = PythonActivity.mActivity

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toLanguageTag()
            )
            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, True)

            recognizer = SpeechRecognizer.createSpeechRecognizer(activity)

            class Listener(PythonJavaClass):
                __javainterfaces__ = ["android/speech/RecognitionListener"]
                __javacontext__ = "app"

                def __init__(self, outer):
                    super().__init__()
                    self.outer = outer

                @java_method("(Landroid/os/Bundle;)V")
                def onResults(self, bundle):
                    SpeechRecognizer_RESULTS_KEY = "results_recognition"
                    matches = bundle.getStringArrayList(SpeechRecognizer_RESULTS_KEY)
                    raw_audio = bytes(self.outer._audio_buffer)
                    if matches and matches.size() > 0:
                        self.outer.on_result(matches.get(0), raw_audio)
                    else:
                        self.outer.on_error("No speech detected")

                @java_method("(I)V")
                def onError(self, error_code):
                    self.outer.on_error(f"code {error_code}")

                @java_method("(Landroid/os/Bundle;)V")
                def onReadyForSpeech(self, bundle):
                    pass

                @java_method("(F)V")
                def onRmsChanged(self, rms):
                    pass

                @java_method("([B)V")
                def onBufferReceived(self, buffer):
                    try:
                        self.outer._audio_buffer.extend(bytes(buffer))
                    except Exception:
                        pass  # best-effort; voiceprint check is skipped if this fails

                @java_method("()V")
                def onEndOfSpeech(self):
                    pass

                @java_method("(I)V")
                def onEvent(self, event_type):
                    pass

                @java_method("(Landroid/os/Bundle;)V")
                def onPartialResults(self, bundle):
                    pass

                @java_method("()V")
                def onBeginningOfSpeech(self):
                    pass

            listener = Listener(self)
            recognizer.setRecognitionListener(listener)
            recognizer.startListening(intent)

        except Exception as exc:  # noqa: BLE001
            self.on_error(str(exc))

    # ---------------- Desktop (dev/testing) ----------------

    def _listen_desktop(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.on_error(
                "speech_recognition not installed. "
                "Run: pip install SpeechRecognition pyaudio"
            )
            return

        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=6)
            text = recognizer.recognize_google(audio)
            raw_audio = audio.get_raw_data(convert_rate=16000, convert_width=2)
            self.on_result(text, raw_audio)
        except sr.WaitTimeoutError:
            self.on_error("No speech detected (timeout)")
        except sr.UnknownValueError:
            self.on_error("Could not understand audio")
        except Exception as exc:  # noqa: BLE001
            self.on_error(str(exc))
