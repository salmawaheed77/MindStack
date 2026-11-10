"""Icons drawn with QPainter so the project needs no image assets."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)


def draw_mic(p: QPainter, cx: float, cy: float, size: float, color: QColor) -> None:
    """Draw a simple microphone glyph centred at (cx, cy); `size` = glyph height."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    w = size * 0.36
    body = QRectF(cx - w / 2, cy - size * 0.5, w, size * 0.62)
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawRoundedRect(body, w / 2, w / 2)

    pen = QPen(color, max(1.5, size * 0.07))
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    arc = QRectF(cx - size * 0.3, cy - size * 0.32, size * 0.6, size * 0.6)
    path = QPainterPath()
    path.arcMoveTo(arc, 180)
    path.arcTo(arc, 180, 180)
    p.drawPath(path)
    p.drawLine(QPointF(cx, cy + size * 0.28), QPointF(cx, cy + size * 0.46))
    p.drawLine(QPointF(cx - size * 0.15, cy + size * 0.46),
               QPointF(cx + size * 0.15, cy + size * 0.46))
    p.restore()


def make_app_icon(size: int = 64) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    grad = QRadialGradient(QPointF(size * 0.4, size * 0.35), size * 0.7)
    grad.setColorAt(0, QColor("#7DB0FF"))
    grad.setColorAt(1, QColor("#2F6FED"))
    p.setPen(Qt.NoPen)
    p.setBrush(grad)
    p.drawEllipse(QRectF(2, 2, size - 4, size - 4))
    draw_mic(p, size / 2, size / 2, size * 0.5, QColor("white"))
    p.end()
    return QIcon(pm)
