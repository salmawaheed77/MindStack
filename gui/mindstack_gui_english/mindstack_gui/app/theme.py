"""Dark / light themes (QSS) and small style helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path
from string import Template

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

PALETTES = {
    "dark": dict(
        bg="#0E1117", surface="#161B24", surface2="#1D2430", border="#2A3242",
        text="#E8ECF4", muted="#8B95A8", accent="#4F8CFF", accent_hover="#6AA0FF",
        accent_text="#FFFFFF", success="#2ECC8F", danger="#FF5C6C", warning="#F5B942",
        selection="#24324F", nav_checked="#1F2A44",
    ),
    "light": dict(
        bg="#F3F5F9", surface="#FFFFFF", surface2="#EEF1F6", border="#D9DFEA",
        text="#1B2230", muted="#6B7588", accent="#2F6FED", accent_hover="#4C84F5",
        accent_text="#FFFFFF", success="#14A06F", danger="#E5384B", warning="#D99A12",
        selection="#DCE7FD", nav_checked="#E3ECFD",
    ),
}

_QSS = Template("""
* { font-size: 13px; }
QWidget { background: $bg; color: $text; }
QMainWindow, QDialog, QStackedWidget, QStackedWidget > QWidget { background: $bg; }
QToolTip { background: $surface2; color: $text; border: 1px solid $border; padding: 4px; }
QStatusBar { background: $surface; color: $muted; border-top: 1px solid $border; }
QStatusBar::item { border: none; }

/* ---------- sidebar ---------- */
#Sidebar { background: $surface; border-right: 1px solid $border; }
#Sidebar QLabel { background: transparent; }
#Brand { font-size: 20px; font-weight: 700; color: $text; }
#BrandSub { color: $muted; font-size: 11px; }
QPushButton#NavButton {
    background: transparent; border: none; border-radius: 10px;
    text-align: left; padding: 11px 14px; color: $muted; font-weight: 600;
}
QPushButton#NavButton:hover { background: $surface2; color: $text; }
QPushButton#NavButton:checked { background: $nav_checked; color: $accent; }
#StatusChip { background: $surface2; border: 1px solid $border; border-radius: 10px; }
#StatusChip QLabel { background: transparent; }

/* ---------- cards & text ---------- */
QFrame#Card { background: $surface; border: 1px solid $border; border-radius: 14px; }
QFrame#Card QLabel { background: transparent; }
#PageTitle { font-size: 22px; font-weight: 700; }
#PageSub { color: $muted; }
#CardTitle { color: $muted; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
#StateLabel { font-size: 22px; font-weight: 700; }
#Muted { color: $muted; }
#BigText { font-size: 18px; font-weight: 600; }
#ResultText { font-size: 18px; font-weight: 600; }
#ResultText[status="ok"] { color: $success; }
#ResultText[status="fail"] { color: $danger; }

/* ---------- buttons ---------- */
QPushButton {
    background: $surface2; border: 1px solid $border; border-radius: 9px;
    padding: 8px 16px; font-weight: 600;
}
QPushButton:hover { border-color: $accent; }
QPushButton:pressed { background: $selection; }
QPushButton:disabled { color: $muted; border-color: $border; background: $surface; }
QPushButton[variant="primary"] {
    background: $accent; color: $accent_text; border: none;
}
QPushButton[variant="primary"]:hover { background: $accent_hover; }
QPushButton[variant="primary"]:disabled { background: $border; color: $muted; }
QPushButton[variant="danger"] { background: $danger; color: #FFFFFF; border: none; }
QPushButton[variant="danger"]:hover { background: $danger; }
QPushButton#MicButton { font-size: 15px; padding: 12px 28px; border-radius: 12px; }
QPushButton#MicButton[listening="true"] { background: $danger; }

/* ---------- inputs ---------- */
QLineEdit, QComboBox {
    background: $surface2; border: 1px solid $border; border-radius: 9px;
    padding: 8px 12px; selection-background-color: $accent;
}
QLineEdit:focus, QComboBox:focus { border-color: $accent; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: $surface; border: 1px solid $border; selection-background-color: $selection;
    selection-color: $text; outline: none;
}
QCheckBox { spacing: 10px; background: transparent; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid $border; background: $surface2; }
QCheckBox::indicator:checked { background: $accent; border-color: $accent; image: url($check_icon); }
QSlider::groove:horizontal { height: 6px; background: $surface2; border-radius: 3px; }
QSlider::sub-page:horizontal { background: $accent; border-radius: 3px; }
QSlider::handle:horizontal { background: $text; width: 16px; margin: -6px 0; border-radius: 8px; }

/* ---------- progress ---------- */
QProgressBar { background: $surface2; border: none; border-radius: 5px; height: 10px;
    text-align: center; color: transparent; }
QProgressBar::chunk { background: $accent; border-radius: 5px; }
QProgressBar[level="high"]::chunk { background: $danger; }
QProgressBar[level="mid"]::chunk { background: $warning; }

/* ---------- lists / tables / trees ---------- */
QTableView, QTreeWidget, QListWidget {
    background: $surface; alternate-background-color: $surface2; border: 1px solid $border;
    border-radius: 10px; gridline-color: transparent; outline: none;
    selection-background-color: $selection; selection-color: $text;
}
QTableView::item, QTreeWidget::item, QListWidget::item { padding: 6px 8px; border: none; }
QListWidget#RecentList { border: none; background: transparent; }
QListWidget#RecentList::item { border-bottom: 1px solid $border; padding: 8px 4px; }
QHeaderView::section {
    background: $surface; color: $muted; border: none; border-bottom: 1px solid $border;
    padding: 8px; font-weight: 700;
}
QTableCornerButton::section { background: $surface; border: none; }

/* ---------- group boxes (settings) ---------- */
QGroupBox {
    background: $surface; border: 1px solid $border; border-radius: 14px;
    margin-top: 14px; padding: 18px 16px 14px 16px; font-weight: 700;
}
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 6px; color: $muted;
    background: $bg; }
QGroupBox QLabel, QGroupBox QCheckBox { background: transparent; font-weight: 400; }

/* ---------- scrollbars ---------- */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $border; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: $muted; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: $border; border-radius: 4px; min-width: 30px; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QMessageBox { background: $bg; }
""")


def _check_icon_path() -> str:
    """Draw the white check mark once and return its path (QSS needs a file)."""
    path = Path(tempfile.gettempdir()) / "mindstack_check.png"
    if not path.exists():
        pm = QPixmap(18, 18)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("white"), 2.4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawPolyline([QPointF(4.5, 9.5), QPointF(7.8, 12.8), QPointF(13.5, 5.8)])
        p.end()
        pm.save(str(path))
    return path.as_posix()


def apply_theme(app: QApplication, name: str) -> dict:
    palette = PALETTES.get(name, PALETTES["dark"])
    app.setStyleSheet(_QSS.substitute(palette, check_icon=_check_icon_path()))
    return palette


def setup_fonts(app: QApplication) -> None:
    """Pick the first installed family that also renders Arabic well."""
    from PySide6.QtGui import QFontDatabase

    available = set(QFontDatabase.families())
    for family in ("Segoe UI", "Cairo", "Noto Sans Arabic", "Noto Sans", "Ubuntu", "DejaVu Sans"):
        if family in available:
            font = QFont(family)
            font.setPointSize(10)
            app.setFont(font)
            return


def repolish(widget: QWidget) -> None:
    """Re-apply the stylesheet after a dynamic property changed."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
