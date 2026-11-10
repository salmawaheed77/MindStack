"""Microphone level test."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from ..controller import Controller
from ..theme import repolish


class MicTestDialog(QDialog):
    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.ctl = controller
        self.setWindowTitle("Microphone test")
        self.setModal(True)
        self.setMinimumWidth(420)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)

        title = QLabel("Say something…")
        title.setObjectName("BigText")
        lay.addWidget(title)
        hint = QLabel("The bar should move while you speak. "
                      "If it stays empty, pick another microphone in Settings.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(14)
        lay.addWidget(self.bar)

        self.status = QLabel("Waiting for sound…")
        self.status.setObjectName("Muted")
        lay.addWidget(self.status)
        lay.addSpacing(6)

        row = QHBoxLayout()
        row.addStretch(1)
        close = QPushButton("Done")
        close.setProperty("variant", "primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)

        self.ctl.mic_level.connect(self._on_level)
        self.finished.connect(self._stop)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.ctl.start_mic_test()

    def _stop(self, _result: int) -> None:
        self.ctl.stop_mic_test()
        try:
            self.ctl.mic_level.disconnect(self._on_level)
        except (RuntimeError, TypeError):
            pass

    def _on_level(self, level: float) -> None:
        pct = int(level * 100)
        self.bar.setValue(pct)
        state = "high" if pct > 85 else "mid" if pct > 65 else "ok"
        if self.bar.property("level") != state:
            self.bar.setProperty("level", state)
            repolish(self.bar)
        self.status.setText("Microphone is working ✓" if pct > 8 else "Waiting for sound…")
