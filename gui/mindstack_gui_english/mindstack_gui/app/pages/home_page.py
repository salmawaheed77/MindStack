"""Home: live status, recognized command, result, quick input and stats."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..controller import Controller
from ..models import CommandRecord
from ..state import STATE_INFO, AppState
from ..theme import repolish
from ..widgets.common import Card, page_header
from ..widgets.status_orb import StatusOrb
from ..widgets.system_stats import SystemStats

RECENT_COUNT = 6


class HomePage(QWidget):
    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.ctl = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)
        root.addWidget(page_header(
            "Home", "Speak a command and watch it go from voice to Linux operation."))

        cols = QHBoxLayout()
        cols.setSpacing(18)
        root.addLayout(cols, 1)

        left = QVBoxLayout()
        left.setSpacing(14)
        cols.addLayout(left, 3)
        right = QVBoxLayout()
        right.setSpacing(14)
        cols.addLayout(right, 2)

        # ---- status card -----------------------------------------------------
        status = Card()
        self.orb = StatusOrb()
        self.state_label = QLabel()
        self.state_label.setObjectName("StateLabel")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.hint_label = QLabel()
        self.hint_label.setObjectName("Muted")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)

        self.mic_button = QPushButton()
        self.mic_button.setObjectName("MicButton")
        self.mic_button.setProperty("variant", "primary")
        self.mic_button.setCursor(Qt.PointingHandCursor)
        self.mic_button.clicked.connect(self.ctl.toggle_listening)

        status.body.addWidget(self.orb, 1)
        status.body.addWidget(self.state_label)
        status.body.addWidget(self.hint_label)
        status.body.addSpacing(6)
        status.body.addWidget(self.mic_button, 0, Qt.AlignHCenter)
        left.addWidget(status, 1)

        # ---- command / result ------------------------------------------------
        io_row = QHBoxLayout()
        io_row.setSpacing(14)
        cmd_card = Card("Recognized command")
        self.cmd_label = QLabel("—")
        self.cmd_label.setObjectName("BigText")
        self.cmd_label.setWordWrap(True)
        self.cmd_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cmd_card.body.addWidget(self.cmd_label)

        res_card = Card("Result")
        self.result_label = QLabel("—")
        self.result_label.setObjectName("ResultText")
        self.result_label.setWordWrap(True)
        self.result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        res_card.body.addWidget(self.result_label)
        io_row.addWidget(cmd_card, 1)
        io_row.addWidget(res_card, 1)
        left.addLayout(io_row)

        # ---- typed command ---------------------------------------------------
        type_card = Card("Type a command (no microphone needed)")
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("e.g. open browser   /   show cpu usage")
        self.input.returnPressed.connect(self._send_text)
        send = QPushButton("Send")
        send.setProperty("variant", "primary")
        send.clicked.connect(self._send_text)
        row.addWidget(self.input, 1)
        row.addWidget(send)
        type_card.body.addLayout(row)
        left.addWidget(type_card)

        # ---- right column ----------------------------------------------------
        stats_card = Card("System")
        stats_card.body.addWidget(SystemStats())
        right.addWidget(stats_card)

        recent_card = Card("Recent commands")
        self.recent = QListWidget()
        self.recent.setObjectName("RecentList")
        self.recent.setSelectionMode(QListWidget.NoSelection)
        self.recent.setFocusPolicy(Qt.NoFocus)
        recent_card.body.addWidget(self.recent, 1)
        right.addWidget(recent_card, 1)

        # ---- wiring ----------------------------------------------------------
        self.ctl.state_changed.connect(self._on_state)
        self.ctl.command_recognized.connect(self.cmd_label.setText)
        self.ctl.result_ready.connect(self._on_result)
        self.ctl.record_added.connect(self._add_recent)

        for rec in reversed(self.ctl.history.records()[:RECENT_COUNT]):
            self._add_recent(rec)
        self._on_state(self.ctl.state)

    # ------------------------------------------------------------------ slots
    def _send_text(self) -> None:
        text = self.input.text()
        if text.strip():
            self.input.clear()
            self.ctl.submit_text(text)

    def _on_state(self, state: AppState) -> None:
        title, hint = STATE_INFO[state]
        self.orb.set_state(state)
        self.state_label.setText(title)
        self.hint_label.setText(hint)

        listening = state is AppState.LISTENING
        self.mic_button.setText("Stop listening" if listening else "Start listening")
        self.mic_button.setProperty("listening", listening)
        repolish(self.mic_button)
        self.mic_button.setEnabled(
            state in (AppState.IDLE, AppState.LISTENING, AppState.ERROR))

        if listening:
            self.cmd_label.setText("…")
            self._set_result("—", None)
        elif state is AppState.PROCESSING:
            self._set_result("Working on it…", None)

    def _on_result(self, message: str, success: bool) -> None:
        self._set_result(message, success)

    def _set_result(self, text: str, success: bool | None) -> None:
        self.result_label.setText(text)
        self.result_label.setProperty(
            "status", "" if success is None else "ok" if success else "fail")
        repolish(self.result_label)

    def _add_recent(self, rec: CommandRecord) -> None:
        mark = "✓" if rec.success else "✗"
        item = QListWidgetItem(f"{mark}  {rec.text}\n     {rec.result}")
        item.setToolTip(rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        self.recent.insertItem(0, item)
        while self.recent.count() > RECENT_COUNT:
            self.recent.takeItem(self.recent.count() - 1)
