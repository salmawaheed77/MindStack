"""Confirmation before a dangerous command (delete, shutdown, ...)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class ConfirmDialog(QDialog):
    def __init__(self, command_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm command")
        self.setModal(True)
        self.setMinimumWidth(420)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)

        title = QLabel("⚠  This command can change or remove data")
        title.setObjectName("BigText")
        title.setWordWrap(True)
        lay.addWidget(title)

        lay.addWidget(QLabel("The system understood:"))
        cmd = QLabel(command_text)
        cmd.setObjectName("BigText")
        cmd.setWordWrap(True)
        cmd.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(cmd)

        ask = QLabel("Do you want to run it?")
        ask.setObjectName("Muted")
        lay.addWidget(ask)
        lay.addSpacing(6)

        row = QHBoxLayout()
        row.addStretch(1)
        self.no_btn = QPushButton("No, cancel")
        self.yes_btn = QPushButton("Yes, run it")
        self.yes_btn.setProperty("variant", "danger")
        self.no_btn.setDefault(True)          # Enter = safe choice
        self.no_btn.clicked.connect(self.reject)
        self.yes_btn.clicked.connect(self.accept)
        row.addWidget(self.no_btn)
        row.addWidget(self.yes_btn)
        lay.addLayout(row)
