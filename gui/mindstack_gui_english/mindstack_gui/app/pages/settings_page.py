"""Settings: audio, recognition, voice reply, safety and appearance."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..models import SettingsStore
from ..widgets.common import page_header

try:  # QtMultimedia is optional; fall back to "system default"
    from PySide6.QtMultimedia import QMediaDevices
except Exception:  # pragma: no cover
    QMediaDevices = None


def _input_devices() -> list[str]:
    # Headless / CI runs have no audio server and Qt can crash while probing it.
    if QMediaDevices is None or os.environ.get("MINDSTACK_SKIP_AUDIO") \
            or os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        return []
    try:
        return [d.description() for d in QMediaDevices.audioInputs()]
    except Exception:  # pragma: no cover
        return []


class SettingsPage(QWidget):
    def __init__(self, settings: SettingsStore, on_mic_test, parent=None):
        super().__init__(parent)
        self.s = settings

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)
        outer.addWidget(page_header("Settings", "Changes are saved automatically."))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        outer.addWidget(scroll, 1)
        content = QWidget()
        content.setObjectName("SettingsContent")
        content.setStyleSheet("#SettingsContent { background: transparent; }")
        scroll.setWidget(content)
        col = QVBoxLayout(content)
        col.setContentsMargins(0, 0, 8, 0)
        col.setSpacing(6)

        # ---- audio input -----------------------------------------------------
        g = QGroupBox("Audio input")
        f = self._form(g)
        self.mic = QComboBox()
        self.mic.addItem("System default", "")
        for name in _input_devices():
            self.mic.addItem(name, name)
        self._select(self.mic, self.s.get("mic_device"))
        test = QPushButton("Test microphone")
        test.clicked.connect(on_mic_test)
        row = QHBoxLayout()
        row.addWidget(self.mic, 1)
        row.addWidget(test)
        f.addRow("Microphone", row)
        col.addWidget(g)

        # ---- recognition -----------------------------------------------------
        g = QGroupBox("Speech recognition")
        f = self._form(g)
        self.language = QComboBox()
        self.language.addItem("English", "en")
        self.language.addItem("Arabic", "ar")
        self._select(self.language, self.s.get("language"))
        self.engine = QComboBox()
        self.engine.addItems(["Vosk", "SpeechRecognition"])
        self._select(self.engine, self.s.get("engine"))
        f.addRow("Language", self.language)
        f.addRow("Engine", self.engine)
        col.addWidget(g)

        # ---- voice reply -----------------------------------------------------
        g = QGroupBox("Voice reply")
        f = self._form(g)
        self.tts = QCheckBox("Speak the result aloud")
        self.tts.setChecked(self.s.get("tts_enabled"))
        self.rate = QSlider(Qt.Horizontal)
        self.rate.setRange(100, 250)
        self.rate.setValue(self.s.get("tts_rate"))
        self.rate_label = QLabel()
        self.rate_label.setMinimumWidth(80)
        rate_row = QHBoxLayout()
        rate_row.addWidget(self.rate, 1)
        rate_row.addWidget(self.rate_label)
        f.addRow(self.tts)
        f.addRow("Speech rate", rate_row)
        col.addWidget(g)

        # ---- safety ----------------------------------------------------------
        g = QGroupBox("Safety")
        f = self._form(g)
        self.confirm = QCheckBox("Ask for confirmation before dangerous commands (recommended)")
        self.confirm.setChecked(self.s.get("confirm_dangerous"))
        f.addRow(self.confirm)
        col.addWidget(g)

        # ---- appearance ------------------------------------------------------
        g = QGroupBox("Appearance")
        f = self._form(g)
        self.theme = QComboBox()
        self.theme.addItem("Dark", "dark")
        self.theme.addItem("Light", "light")
        self._select(self.theme, self.s.get("theme"))
        f.addRow("Theme", self.theme)
        col.addWidget(g)

        reset = QPushButton("Reset to defaults")
        reset.clicked.connect(self._reset)
        col.addWidget(reset, 0, Qt.AlignLeft)
        col.addStretch(1)

        # ---- wiring (apply on change) ---------------------------------------
        self.mic.currentIndexChanged.connect(
            lambda _i: self.s.set("mic_device", self.mic.currentData()))
        self.language.currentIndexChanged.connect(
            lambda _i: self.s.set("language", self.language.currentData()))
        self.engine.currentTextChanged.connect(lambda t: self.s.set("engine", t))
        self.tts.toggled.connect(lambda v: self.s.set("tts_enabled", v))
        self.tts.toggled.connect(self.rate.setEnabled)
        self.rate.valueChanged.connect(lambda v: self.s.set("tts_rate", v))
        self.rate.valueChanged.connect(self._update_rate_label)
        self.confirm.toggled.connect(lambda v: self.s.set("confirm_dangerous", v))
        self.theme.currentIndexChanged.connect(
            lambda _i: self.s.set("theme", self.theme.currentData()))

        self.rate.setEnabled(self.tts.isChecked())
        self._update_rate_label(self.rate.value())

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _form(group: QGroupBox) -> QFormLayout:
        f = QFormLayout(group)
        f.setHorizontalSpacing(24)
        f.setVerticalSpacing(12)
        f.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        f.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        return f

    @staticmethod
    def _select(combo: QComboBox, value) -> None:
        idx = combo.findData(value)
        if idx < 0:
            idx = combo.findText(str(value))
        combo.setCurrentIndex(max(idx, 0))

    def _update_rate_label(self, v: int) -> None:
        self.rate_label.setText(f"{v} wpm")

    def _reset(self) -> None:
        self.s.reset()
        self._select(self.mic, self.s.get("mic_device"))
        self._select(self.language, self.s.get("language"))
        self._select(self.engine, self.s.get("engine"))
        self.tts.setChecked(self.s.get("tts_enabled"))
        self.rate.setValue(self.s.get("tts_rate"))
        self.confirm.setChecked(self.s.get("confirm_dangerous"))
        self._select(self.theme, self.s.get("theme"))
