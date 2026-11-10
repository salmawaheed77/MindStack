"""Backend interface between the GUI and the rest of the MindStack pipeline.

    Microphone -> Speech-to-Text -> Command Understanding -> Validation
               -> Linux Operation -> Result -> Text-to-Speech

The GUI never talks to Vosk / subprocess / pyttsx3 directly. It only talks to a
`BaseBackend`. Your teammates implement the real one (same signals + methods)
and you pass it to `Controller(...)` in main.py. Until then `MockBackend`
simulates the whole pipeline so the GUI can be developed and demoed alone.
"""

from __future__ import annotations

import random

from PySide6.QtCore import QObject, QTimer, Signal

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


class BaseBackend(QObject):
    """Contract every backend must follow."""

    # --- signals the backend EMITS (GUI listens) ---
    recognized = Signal(str)             # speech-to-text produced a phrase
    needs_confirmation = Signal(str)     # dangerous command, ask the user
    executed = Signal(str, bool)         # (result message, success)
    speaking_done = Signal()             # text-to-speech finished
    error = Signal(str)                  # fatal problem (mic missing, ...)
    mic_level = Signal(float)            # 0.0 .. 1.0, only during mic test

    # --- methods the GUI CALLS (implement all of them) ---
    def start_listening(self, language: str, mic_device: str = "") -> None: ...
    def stop_listening(self) -> None: ...
    def process(self, text: str) -> None:
        """Understand + validate + execute `text`, then emit `executed`
        (or `needs_confirmation` first for dangerous commands)."""
    def confirm(self, accepted: bool) -> None:
        """Answer to a previous `needs_confirmation`."""
    def speak(self, text: str, rate: int = 170) -> None:
        """Say `text` aloud, then emit `speaking_done`."""
    def start_mic_test(self, mic_device: str = "") -> None: ...
    def stop_mic_test(self) -> None: ...
    def shutdown(self) -> None: ...


# --------------------------------------------------------------------------- #
# Mock implementation (no microphone / no real OS operations)
# --------------------------------------------------------------------------- #
SAMPLE_PHRASES = [
    "open browser",
    "list files",
    "show cpu usage",
    "show ram usage",
    "show processes",
    "delete file notes",
]


def _cpu() -> str:
    pct = psutil.cpu_percent(interval=None) if psutil else random.randint(8, 55)
    return f"CPU usage is {pct:.0f} percent"


def _ram() -> str:
    pct = psutil.virtual_memory().percent if psutil else random.randint(30, 70)
    return f"RAM usage is {pct:.0f} percent"


def _disk() -> str:
    pct = psutil.disk_usage("/").percent if psutil else random.randint(20, 80)
    return f"Disk usage is {pct:.0f} percent"


def _procs() -> str:
    n = len(psutil.pids()) if psutil else random.randint(120, 260)
    return f"There are {n} running processes"


# (keywords, answer-or-callable) - first match wins, order matters.
_RULES = [
    (("create file", "new file", "make file"), "File created"),
    (("create folder", "new folder", "make folder"), "Folder created"),
    (("rename",), "File renamed"),
    (("list files", "show files", "list the files"), "There are 12 files in the current folder"),
    (("open",), "Application opened"),
    (("close",), "Application closed"),
    (("process",), _procs),
    (("cpu",), _cpu),
    (("ram", "memory"), _ram),
    (("disk", "storage"), _disk),
]
_DANGEROUS = ("delete", "remove", "erase")


class MockBackend(BaseBackend):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending_delete: str | None = None

        self._t_listen = self._timer(self._on_listen_done)
        self._t_process = self._timer(self._on_process_done)
        self._t_confirm = self._timer(self._on_confirm_done)
        self._t_speak = self._timer(self.speaking_done.emit)

        self._t_level = QTimer(self)
        self._t_level.setInterval(60)
        self._t_level.timeout.connect(self._tick_level)
        self._level = 0.0

        self._current = ""
        self._confirm_ok = False

    def _timer(self, slot) -> QTimer:
        t = QTimer(self)
        t.setSingleShot(True)
        t.timeout.connect(slot)
        return t

    # -- listening -----------------------------------------------------------
    def start_listening(self, language="en", mic_device=""):
        self._t_listen.start(2200)

    def stop_listening(self):
        self._t_listen.stop()

    def _on_listen_done(self):
        self.recognized.emit(random.choice(SAMPLE_PHRASES))

    # -- processing ----------------------------------------------------------
    def process(self, text):
        self._current = text
        if any(k in text.lower() for k in _DANGEROUS):
            self._t_process.setProperty("mode", "confirm")
            self._t_process.start(600)
        else:
            self._t_process.setProperty("mode", "run")
            self._t_process.start(900)

    def _on_process_done(self):
        if self._t_process.property("mode") == "confirm":
            self.needs_confirmation.emit(self._current)
            return
        low = self._current.lower()
        for keywords, answer in _RULES:
            if any(k in low for k in keywords):
                self.executed.emit(answer() if callable(answer) else answer, True)
                return
        self.executed.emit("Sorry, I did not understand that command", False)

    def confirm(self, accepted):
        self._confirm_ok = accepted
        self._t_confirm.start(500)

    def _on_confirm_done(self):
        if self._confirm_ok:
            self.executed.emit("File deleted", True)
        else:
            self.executed.emit("Command cancelled", False)

    # -- speaking ------------------------------------------------------------
    def speak(self, text, rate=170):
        self._t_speak.start(900 + len(text) * 25)

    # -- mic test ------------------------------------------------------------
    def start_mic_test(self, mic_device=""):
        self._level = 0.0
        self._t_level.start()

    def stop_mic_test(self):
        self._t_level.stop()
        self.mic_level.emit(0.0)

    def _tick_level(self):
        target = random.random() ** 1.6
        self._level += (target - self._level) * 0.45
        self.mic_level.emit(min(1.0, self._level))

    def shutdown(self):
        for t in (self._t_listen, self._t_process, self._t_confirm,
                  self._t_speak, self._t_level):
            t.stop()
