"""Small reusable building blocks."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class Card(QFrame):
    """Rounded surface with an optional small uppercase title."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 16, 20, 18)
        self.body.setSpacing(10)
        if title:
            lbl = QLabel(title.upper())
            lbl.setObjectName("CardTitle")
            self.body.addWidget(lbl)


def page_header(title: str, subtitle: str = "") -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSub")
        lay.addWidget(s)
    return box
