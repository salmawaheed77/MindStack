"""Real backend: microphone -> Whisper -> Fire -> executor -> text-to-speech.

Every slow job runs in a background thread and reports back with signals,
so the window never freezes.
"""

import sys
import threading
from pathlib import Path

# Make the project root importable (executor/, stt/, tts/, nlp/ live there).
# this file: <root>/gui/mindstack_gui_english/mindstack_gui/app/real_backend.py
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .backend import BaseBackend


def describe(action: dict) -> str:
    """Readable sentence for the confirmation dialog, built from the real action."""
    name = str(action.get("action", "")).replace("_", " ")
    parts = [str(action[k]) for k in
             ("target", "path", "source", "destination", "new_name", "folder")
             if action.get(k)]
    return " ".join([name] + parts).strip()


def speakable(result: dict) -> str:
    """Short text that is nice to hear (message + first items of the data)."""
    msg = result.get("message", "")
    data = result.get("data")
    if isinstance(data, list) and data:
        names = [d.get("name", str(d)) if isinstance(d, dict) else str(d)
                 for d in data[:3]]
        msg += " First items: " + ", ".join(names)
    elif isinstance(data, dict) and "used_percent" in data:
        msg += f" {data['used_percent']} percent."
    elif isinstance(data, str) and len(data) < 60:
        msg += " " + data
    return msg


class RealBackend(BaseBackend):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending = None        # action waiting for the user's yes/no
        self._listening = False
        self._stream = None         # microphone test stream

    @staticmethod
    def _in_thread(fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    # -- listening -----------------------------------------------------------
    def start_listening(self, language="en", mic_device=""):
        if self._listening:
            return                      # a recording is already running
        self._listening = True
        self._in_thread(self._listen_worker, language, mic_device)

    def stop_listening(self):
        was_listening, self._listening = self._listening, False
        if was_listening:
            try:
                from stt.speech_to_text import cancel
                cancel()
            except Exception:
                pass

    def _listen_worker(self, language, mic_device):
        try:
            from stt.speech_to_text import listen_and_transcribe
            text = listen_and_transcribe(
                seconds=5, device=mic_device or None, language=language or None)
        except Exception as exc:
            self._listening = False
            self.error.emit(f"Microphone / speech error: {exc}")
            return
        if not self._listening:
            return                      # the user pressed stop
        self._listening = False
        if text:
            self.recognized.emit(text)
        else:
            self.error.emit("I did not hear anything. Please try again.")

    # -- processing ----------------------------------------------------------
    def process(self, text):
        self._in_thread(self._process_worker, text)

    def _process_worker(self, text):
        try:
            from executor.executor import execute_command
            from nlp.intent import understand
            action = understand(text)                    # Fire -> JSON action
            if action.get("action") == "unknown":
                self.executed.emit("Sorry, I did not understand that command", False)
                return
            result = execute_command(action)
        except Exception as exc:
            self.executed.emit(f"Error: {exc}", False)
            return
        if result.get("error") == "confirmation_required":
            self._pending = action
            self.needs_confirmation.emit(describe(action))
            return
        self.executed.emit(speakable(result), bool(result.get("success")))

    def confirm(self, accepted):
        pending, self._pending = self._pending, None
        if not accepted or pending is None:
            self.executed.emit("Command cancelled", False)
            return
        self._in_thread(self._confirm_worker, pending)

    def _confirm_worker(self, action):
        try:
            from executor.executor import execute_command
            result = execute_command(action, confirmed=True)
            self.executed.emit(speakable(result), bool(result.get("success")))
        except Exception as exc:
            self.executed.emit(f"Error: {exc}", False)

    # -- speaking ------------------------------------------------------------
    def speak(self, text, rate=170):
        self._in_thread(self._speak_worker, text, rate)

    def _speak_worker(self, text, rate):
        try:
            from tts.tts import speak
            speak(text, rate)
        except Exception as exc:
            print(f"TTS error: {exc}")
        finally:
            self.speaking_done.emit()

    # -- microphone test -----------------------------------------------------
    def start_mic_test(self, mic_device=""):
        try:
            import numpy as np
            import sounddevice as sd

            def callback(indata, frames, time, status):
                level = float(np.sqrt(np.mean(indata ** 2)))
                self.mic_level.emit(min(1.0, level * 8))

            self._stream = sd.InputStream(
                channels=1, callback=callback, device=mic_device or None)
            self._stream.start()
        except Exception as exc:
            self.error.emit(f"Microphone test failed: {exc}")

    def stop_mic_test(self):
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        self.mic_level.emit(0.0)

    def shutdown(self):
        self._listening = False
        self.stop_mic_test()
