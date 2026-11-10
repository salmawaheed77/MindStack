"""Help page: every supported command with an example you can try with a click."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..commands_data import COMMAND_CATALOG
from ..widgets.common import page_header

PHRASE_ROLE = Qt.UserRole + 1


class CommandsPage(QWidget):
    try_phrase = Signal(str)   # emitted when the user wants to run an example

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)
        root.addWidget(page_header(
            "Supported commands",
            "Say these phrases (or similar ones). Double-click an example to try it."))

        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search commands…")
        self.search.setClearButtonEnabled(True)
        self.try_btn = QPushButton("Try selected example")
        self.try_btn.setProperty("variant", "primary")
        self.try_btn.setEnabled(False)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.try_btn)
        root.addLayout(bar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Command", "Example phrase", "What it does"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setIndentation(18)
        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        root.addWidget(self.tree, 1)

        self.legend = QLabel("⚠  = asks for confirmation before running")
        self.legend.setObjectName("Muted")
        root.addWidget(self.legend)

        self._populate()
        self.search.textChanged.connect(self._filter)
        self.tree.itemSelectionChanged.connect(self._on_select)
        self.tree.itemDoubleClicked.connect(lambda item, _c: self._emit(item))
        self.try_btn.clicked.connect(lambda: self._emit(self.tree.currentItem()))

    def _populate(self) -> None:
        for category, commands in COMMAND_CATALOG:
            parent = QTreeWidgetItem([category])
            font = parent.font(0)
            font.setBold(True)
            parent.setFont(0, font)
            parent.setFlags(Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(parent)
            for name, phrase, desc, dangerous in commands:
                label = f"⚠  {name}" if dangerous else name
                item = QTreeWidgetItem([label, phrase, desc])
                item.setData(1, PHRASE_ROLE, phrase)
                item.setTextAlignment(1, Qt.AlignLeft | Qt.AlignVCenter)
                if dangerous:
                    item.setForeground(0, QBrush(QColor("#F5B942")))
                parent.addChild(item)
            parent.setExpanded(True)

    def _filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            visible = 0
            for j in range(parent.childCount()):
                child = parent.child(j)
                hit = not needle or any(
                    needle in child.text(c).lower() for c in range(3))
                child.setHidden(not hit)
                visible += hit
            parent.setHidden(visible == 0)
            if needle and visible:
                parent.setExpanded(True)

    def _on_select(self) -> None:
        item = self.tree.currentItem()
        self.try_btn.setEnabled(bool(item and item.data(1, PHRASE_ROLE)))

    def _emit(self, item) -> None:
        if item is not None:
            phrase = item.data(1, PHRASE_ROLE)
            if phrase:
                self.try_phrase.emit(phrase)
