"""Command log: searchable, filterable, sortable history with CSV export."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..controller import Controller
from ..models import HistoryFilterProxy
from ..widgets.common import page_header


class LogPage(QWidget):
    def __init__(self, controller: Controller, notify=None, parent=None):
        """`notify(text)` is an optional callback for short status messages."""
        super().__init__(parent)
        self.ctl = controller
        self._notify = notify or (lambda _t: None)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)
        root.addWidget(page_header(
            "Command log", "Every command the system understood, with its result."))

        # ---- toolbar ---------------------------------------------------------
        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search commands and results…")
        self.search.setClearButtonEnabled(True)
        self.filter = QComboBox()
        self.filter.addItem("All", "all")
        self.filter.addItem("Success only", "success")
        self.filter.addItem("Failed only", "failed")
        self.export_btn = QPushButton("Export CSV")
        self.clear_btn = QPushButton("Clear log")
        self.clear_btn.setProperty("variant", "danger")
        bar.addWidget(self.search, 1)
        bar.addWidget(self.filter)
        bar.addWidget(self.export_btn)
        bar.addWidget(self.clear_btn)
        root.addLayout(bar)

        # ---- table -----------------------------------------------------------
        self.proxy = HistoryFilterProxy(self)
        self.proxy.setSourceModel(self.ctl.history)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.sortByColumn(0, Qt.DescendingOrder)
        hh = self.table.horizontalHeader()
        hh.setHighlightSections(False)
        hh.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

        self.empty_label = QLabel("No commands yet. Say something or type a command on the Home page.")
        self.empty_label.setObjectName("Muted")
        self.empty_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.empty_label)

        self.count_label = QLabel()
        self.count_label.setObjectName("Muted")
        root.addWidget(self.count_label)

        # ---- wiring ----------------------------------------------------------
        self.search.textChanged.connect(self.proxy.set_text)
        self.filter.currentIndexChanged.connect(
            lambda _i: self.proxy.set_status(self.filter.currentData()))
        self.export_btn.clicked.connect(self._export)
        self.clear_btn.clicked.connect(self._clear)
        for sig in (self.proxy.rowsInserted, self.proxy.rowsRemoved,
                    self.proxy.modelReset, self.proxy.layoutChanged):
            sig.connect(self._refresh_footer)
        self._refresh_footer()

    # ------------------------------------------------------------------ slots
    def _refresh_footer(self, *_args) -> None:
        shown = self.proxy.rowCount()
        total = self.ctl.history.rowCount()
        self.empty_label.setVisible(total == 0)
        self.table.setVisible(total != 0)
        self.count_label.setText(
            f"Showing {shown} of {total} commands" if total else "")
        self.export_btn.setEnabled(total > 0)
        self.clear_btn.setEnabled(total > 0)

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export command log", "mindstack_log.csv", "CSV files (*.csv)")
        if not path:
            return
        try:
            n = self.ctl.export_history(path)
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
            return
        self._notify(f"Exported {n} commands to {path}")

    def _clear(self) -> None:
        answer = QMessageBox.question(
            self, "Clear log", "Delete the whole command history? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.ctl.clear_history()
            self._notify("Command log cleared")
