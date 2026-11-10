"""Live CPU / RAM / Disk bars (uses psutil when installed)."""

from __future__ import annotations

import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QLabel, QProgressBar, QWidget

from ..theme import repolish

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


class SystemStats(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)

        self._bars: dict[str, tuple[QProgressBar, QLabel]] = {}
        for row, name in enumerate(("CPU", "RAM", "Disk")):
            label = QLabel(name)
            label.setObjectName("Muted")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setFixedHeight(10)
            value = QLabel("—")
            value.setMinimumWidth(40)
            grid.addWidget(label, row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(value, row, 2)
            self._bars[name] = (bar, value)

        if psutil is None:
            self._bars["CPU"][1].setText("n/a")
            return
        psutil.cpu_percent(interval=None)  # prime the counter
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    def refresh(self) -> None:
        if psutil is None:
            return
        values = {
            "CPU": psutil.cpu_percent(interval=None),
            "RAM": psutil.virtual_memory().percent,
            "Disk": psutil.disk_usage(os.path.abspath(os.sep)).percent,
        }
        for name, pct in values.items():
            bar, label = self._bars[name]
            bar.setValue(int(pct))
            label.setText(f"{pct:.0f}%")
            level = "high" if pct >= 85 else "mid" if pct >= 65 else "ok"
            if bar.property("level") != level:
                bar.setProperty("level", level)
                repolish(bar)
