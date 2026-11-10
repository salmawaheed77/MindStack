"""Controller: the single object every page talks to.

Pages never touch the backend. They call controller methods and listen to
controller signals, so swapping MockBackend for the real backend changes nothing
in the UI code.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, Signal

from .backend import BaseBackend
from .models import CommandRecord, HistoryModel, SettingsStore
from .state import AppState


def default_history_path() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    return Path(base or ".") / "MindStack" / "history.json"


class Controller(QObject):
    state_changed = Signal(object)            # AppState
    command_recognized = Signal(str)
    result_ready = Signal(str, bool)          # message, success
    record_added = Signal(object)             # CommandRecord
    confirmation_requested = Signal(str)      # command text
    error_occurred = Signal(str)
    mic_level = Signal(float)

    def __init__(
        self,
        backend: BaseBackend,
        settings: SettingsStore,
        history_path: Path | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.backend = backend
        self.settings = settings
        self.history = HistoryModel(self)
        self._history_path = history_path or default_history_path()
        self.history.load(self._history_path)

        self._state = AppState.IDLE
        self._current_text = ""

        backend.recognized.connect(self._on_recognized)
        backend.needs_confirmation.connect(self._on_needs_confirmation)
        backend.executed.connect(self._on_executed)
        backend.speaking_done.connect(self._on_speaking_done)
        backend.error.connect(self._on_error)
        backend.mic_level.connect(self.mic_level)

    # ------------------------------------------------------------------ state
    @property
    def state(self) -> AppState:
        return self._state

    def _set_state(self, state: AppState) -> None:
        if state is not self._state:
            self._state = state
            self.state_changed.emit(state)

    # --------------------------------------------------------- user actions
    def toggle_listening(self) -> None:
        if self._state is AppState.LISTENING:
            self.stop_listening()
        elif self._state in (AppState.IDLE, AppState.ERROR):
            self.start_listening()

    def start_listening(self) -> None:
        if self._state not in (AppState.IDLE, AppState.ERROR):
            return
        self._set_state(AppState.LISTENING)
        self.backend.start_listening(
            self.settings.get("language"), self.settings.get("mic_device")
        )

    def stop_listening(self) -> None:
        if self._state is AppState.LISTENING:
            self.backend.stop_listening()
            self._set_state(AppState.IDLE)

    def submit_text(self, text: str) -> None:
        """Run a typed command (testing without a microphone)."""
        text = text.strip()
        if not text or self._state in (AppState.PROCESSING, AppState.SPEAKING):
            return
        if self._state is AppState.LISTENING:
            self.backend.stop_listening()
        self._on_recognized(text)

    def answer_confirmation(self, accepted: bool) -> None:
        self.backend.confirm(accepted)

    # -------------------------------------------------------------- history
    def clear_history(self) -> None:
        self.history.clear()
        self.history.save(self._history_path)

    def export_history(self, path: str) -> int:
        """Write history to CSV (UTF-8 with BOM so Excel shows Arabic). Returns rows."""
        records = self.history.records()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Time", "Command", "Result", "Status"])
            for r in records:
                w.writerow([
                    r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    r.text,
                    r.result,
                    "Success" if r.success else "Failed",
                ])
        return len(records)

    # ------------------------------------------------------------ mic test
    def start_mic_test(self) -> None:
        self.stop_listening()
        self.backend.start_mic_test(self.settings.get("mic_device"))

    def stop_mic_test(self) -> None:
        self.backend.stop_mic_test()

    def shutdown(self) -> None:
        self.backend.shutdown()
        self.history.save(self._history_path)

    # --------------------------------------------------- backend callbacks
    def _on_recognized(self, text: str) -> None:
        self._current_text = text
        self._set_state(AppState.PROCESSING)
        self.command_recognized.emit(text)
        self.backend.process(text)

    def _on_needs_confirmation(self, text: str) -> None:
        if self.settings.get("confirm_dangerous"):
            self.confirmation_requested.emit(text)
        else:
            self.backend.confirm(True)

    def _on_executed(self, message: str, success: bool) -> None:
        rec = CommandRecord(datetime.now(), self._current_text, message, success)
        self.history.add_record(rec)
        self.history.save(self._history_path)
        self.record_added.emit(rec)
        self.result_ready.emit(message, success)
        if self.settings.get("tts_enabled"):
            self._set_state(AppState.SPEAKING)
            self.backend.speak(message, self.settings.get("tts_rate"))
        else:
            self._set_state(AppState.IDLE)

    def _on_speaking_done(self) -> None:
        if self._state is AppState.SPEAKING:
            self._set_state(AppState.IDLE)

    def _on_error(self, message: str) -> None:
        self._set_state(AppState.ERROR)
        self.error_occurred.emit(message)
