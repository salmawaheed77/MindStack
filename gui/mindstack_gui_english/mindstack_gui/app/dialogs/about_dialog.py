"""About dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .. import APP_NAME, APP_SUBTITLE, __version__
from ..icons import make_app_icon


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(440)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(make_app_icon(72).pixmap(72, 72))
        logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(logo)

        name = QLabel(APP_NAME)
        name.setObjectName("PageTitle")
        name.setAlignment(Qt.AlignCenter)
        lay.addWidget(name)

        sub = QLabel(f"{APP_SUBTITLE}  ·  v{__version__}")
        sub.setObjectName("Muted")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)
        lay.addSpacing(10)

        desc = QLabel(
            "A voice-interaction layer over Linux. Speak a command, the app turns it "
            "into a safe Linux operation, runs it, and speaks the result.\n"
            "The Linux kernel is not modified.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        lay.addWidget(desc)
        lay.addSpacing(6)

        tech = QLabel("Built with Python 3 · PySide6 · psutil · Vosk · pyttsx3")
        tech.setObjectName("Muted")
        tech.setAlignment(Qt.AlignCenter)
        lay.addWidget(tech)

        team = QLabel("Operating Systems course project  ·  Team MindStack")
        team.setObjectName("Muted")
        team.setAlignment(Qt.AlignCenter)
        lay.addWidget(team)
        lay.addSpacing(10)

        row = QHBoxLayout()
        row.addStretch(1)
        close = QPushButton("Close")
        close.setProperty("variant", "primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        row.addStretch(1)
        lay.addLayout(row)
