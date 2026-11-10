"""Animated orb that visualises the current AppState."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..icons import draw_mic
from ..state import STATE_COLORS, AppState

_DURATIONS = {
    AppState.LISTENING: 1800,
    AppState.PROCESSING: 1100,
    AppState.SPEAKING: 1000,
    AppState.ERROR: 1600,
}


class StatusOrb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(230, 230)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._state = AppState.IDLE
        self._phase = 0.0

        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._tick)

    def set_state(self, state: AppState) -> None:
        self._state = state
        if state is AppState.IDLE:
            self._anim.stop()
            self._phase = 0.0
        else:
            self._anim.setDuration(_DURATIONS[state])
            if self._anim.state() != QVariantAnimation.Running:
                self._anim.start()
        self.update()

    def _tick(self, value) -> None:
        self._phase = float(value)
        self.update()

    # ------------------------------------------------------------------ paint
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        c = QPointF(self.width() / 2, self.height() / 2)
        r = min(self.width(), self.height()) * 0.20
        color = QColor(STATE_COLORS[self._state])

        if self._state in (AppState.LISTENING, AppState.SPEAKING):
            for i in range(3):
                t = (self._phase + i / 3) % 1.0
                ring = QColor(color)
                ring.setAlpha(int(140 * (1 - t)))
                p.setPen(QPen(ring, 2.5))
                p.setBrush(Qt.NoBrush)
                rad = r * (1.1 + t * 1.0)
                p.drawEllipse(c, rad, rad)

        elif self._state is AppState.PROCESSING:
            track = QColor(color)
            track.setAlpha(50)
            p.setPen(QPen(track, 5))
            p.setBrush(Qt.NoBrush)
            rad = r * 1.45
            p.drawEllipse(c, rad, rad)
            pen = QPen(color, 5)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            rect = QRectF(c.x() - rad, c.y() - rad, rad * 2, rad * 2)
            p.drawArc(rect, int(-self._phase * 360 * 16), 100 * 16)

        elif self._state is AppState.ERROR:
            ring = QColor(color)
            ring.setAlpha(int(70 + 80 * abs(0.5 - self._phase) * 2))
            p.setPen(QPen(ring, 3))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(c, r * 1.5, r * 1.5)

        # soft glow
        glow = QRadialGradient(c, r * 1.9)
        g0 = QColor(color)
        g0.setAlpha(60)
        g1 = QColor(color)
        g1.setAlpha(0)
        glow.setColorAt(0, g0)
        glow.setColorAt(1, g1)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(c, r * 1.9, r * 1.9)

        # core
        core = QRadialGradient(QPointF(c.x() - r * 0.3, c.y() - r * 0.4), r * 1.4)
        core.setColorAt(0, color.lighter(130))
        core.setColorAt(1, color.darker(115))
        p.setBrush(core)
        p.drawEllipse(c, r, r)

        draw_mic(p, c.x(), c.y(), r * 1.05, QColor("white"))
        p.end()
