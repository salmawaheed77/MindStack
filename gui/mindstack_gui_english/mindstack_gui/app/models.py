"""Data models: command history, filtering and persistent settings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QSettings,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QBrush, QColor

MAX_HISTORY = 1000


# --------------------------------------------------------------------------- #
# Command history
# --------------------------------------------------------------------------- #
@dataclass
class CommandRecord:
    timestamp: datetime
    text: str
    result: str
    success: bool

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
            "text": self.text,
            "result": self.result,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CommandRecord":
        return cls(
            timestamp=datetime.fromisoformat(d["timestamp"]),
            text=d["text"],
            result=d["result"],
            success=bool(d["success"]),
        )


SORT_ROLE = Qt.UserRole + 1


class HistoryModel(QAbstractTableModel):
    """Newest-first table model of executed commands."""

    HEADERS = ("Time", "Command", "Result", "Status")
    OK_COLOR = QColor("#2ECC8F")
    FAIL_COLOR = QColor("#FF5C6C")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: list[CommandRecord] = []

    # -- Qt model API -------------------------------------------------------
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._records)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        rec = self._records[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            return (
                rec.timestamp.strftime("%Y-%m-%d  %H:%M:%S"),
                rec.text,
                rec.result,
                "✓  Success" if rec.success else "✗  Failed",
            )[col]
        if role == SORT_ROLE:
            # plain floats / ints / str so QSortFilterProxyModel can compare them
            return (rec.timestamp.timestamp(), rec.text, rec.result, int(rec.success))[col]
        if role == Qt.ForegroundRole and col == 3:
            return QBrush(self.OK_COLOR if rec.success else self.FAIL_COLOR)
        if role == Qt.UserRole:
            return rec
        return None

    # -- mutation -----------------------------------------------------------
    def add_record(self, rec: CommandRecord) -> None:
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._records.insert(0, rec)
        self.endInsertRows()
        if len(self._records) > MAX_HISTORY:
            last = len(self._records) - 1
            self.beginRemoveRows(QModelIndex(), last, last)
            self._records.pop()
            self.endRemoveRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._records.clear()
        self.endResetModel()

    def records(self) -> list[CommandRecord]:
        return list(self._records)

    # -- persistence --------------------------------------------------------
    def save(self, path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = [r.to_dict() for r in self._records]
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
        except OSError:
            pass  # history is a convenience; never crash the GUI over it

    def load(self, path: Path) -> None:
        try:
            raw = json.loads(path.read_text("utf-8"))
            records = [CommandRecord.from_dict(d) for d in raw][:MAX_HISTORY]
        except (OSError, ValueError, KeyError):
            return
        self.beginResetModel()
        self._records = records
        self.endResetModel()


class HistoryFilterProxy(QSortFilterProxyModel):
    """Text search across all columns + status filter (all / success / failed)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._status = "all"
        self.setSortRole(SORT_ROLE)

    def set_text(self, text: str) -> None:
        self._text = text.strip().lower()
        self.invalidateFilter()

    def set_status(self, status: str) -> None:
        self._status = status
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        rec = self.sourceModel().index(row, 0, parent).data(Qt.UserRole)
        if self._status == "success" and not rec.success:
            return False
        if self._status == "failed" and rec.success:
            return False
        if self._text:
            haystack = f"{rec.text} {rec.result}".lower()
            return self._text in haystack
        return True


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
class SettingsStore(QObject):
    """Thin typed wrapper around QSettings that emits `changed(key, value)`."""

    changed = Signal(str, object)

    DEFAULTS = {
        "language": "en",            # speech recognition language: en / ar
        "engine": "Vosk",            # Vosk / SpeechRecognition
        "mic_device": "",            # empty = system default
        "tts_enabled": True,
        "tts_rate": 170,             # words per minute
        "confirm_dangerous": True,
        "theme": "dark",             # dark / light
    }

    def __init__(self, qsettings: QSettings | None = None, parent=None):
        super().__init__(parent)
        self._s = qsettings or QSettings("MindStack", "VoiceLinux")

    def get(self, key: str):
        default = self.DEFAULTS[key]
        value = self._s.value(key, default)
        if isinstance(default, bool):
            return value in (True, "true", "True", "1", 1)
        if isinstance(default, int):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        return value

    def set(self, key: str, value) -> None:
        if key not in self.DEFAULTS or self.get(key) == value:
            return
        self._s.setValue(key, value)
        self.changed.emit(key, value)

    def reset(self) -> None:
        for key, value in self.DEFAULTS.items():
            self.set(key, value)
