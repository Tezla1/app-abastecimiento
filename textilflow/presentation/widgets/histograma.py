"""Histograma con la media y el IC 95 % de la métrica (réplicas de la simulación)."""
from typing import Optional, Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from .. import theme


class Histograma(QWidget):
    def __init__(self, titulo: str = "", parent=None):
        super().__init__(parent)
        self.titulo = titulo
        self._bins: list[tuple] = []
        self._media: Optional[float] = None
        self._ic: Optional[tuple] = None
        self.setMinimumHeight(190)

    def set_datos(self, bins: Sequence[tuple], media: Optional[float], ic: Optional[tuple], titulo: str = "") -> None:
        self._bins, self._media, self._ic = list(bins), media, ic
        if titulo:
            self.titulo = titulo
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(theme.TEXTO))
        p.drawText(QRectF(8, 2, w - 16, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.titulo)
        p.setFont(QFont("Segoe UI", 9))
        if not self._bins:
            p.setPen(QColor(theme.TENUE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Ejecute las réplicas para ver la distribución.")
            return
        izq, der, arr, aba = 40, 14, 30, 30
        zona = QRectF(izq, arr, w - izq - der, h - arr - aba)
        lo, hi = self._bins[0][0], self._bins[-1][1]
        if hi <= lo:
            hi = lo + 1
        nmax = max(n for _, _, n in self._bins) or 1
        for a, b, n in self._bins:
            xa = zona.left() + (a - lo) / (hi - lo) * zona.width()
            xb = zona.left() + (b - lo) / (hi - lo) * zona.width()
            alto = n / nmax * zona.height()
            p.setPen(QPen(QColor(theme.BG), 1))
            p.setBrush(QColor(theme.AZUL))
            p.drawRect(QRectF(xa + 1, zona.bottom() - alto, max(xb - xa - 2, 2), alto))
            if n:
                p.setPen(QColor(theme.TEXTO))
                p.drawText(QRectF(xa, zona.bottom() - alto - 15, xb - xa, 14), Qt.AlignmentFlag.AlignHCenter, str(n))
        p.setPen(QColor(theme.TENUE))
        for i in range(5):
            v = lo + (hi - lo) * i / 4
            xp = zona.left() + zona.width() * i / 4
            p.drawText(QRectF(xp - 30, zona.bottom() + 4, 60, 16), Qt.AlignmentFlag.AlignHCenter, f"{v:.1f}")
        if self._ic and self._ic[0] is not None:
            xa = zona.left() + (self._ic[0] - lo) / (hi - lo) * zona.width()
            xb = zona.left() + (self._ic[1] - lo) / (hi - lo) * zona.width()
            c = QColor(theme.DORADO)
            c.setAlpha(60)
            p.fillRect(QRectF(xa, zona.top(), max(xb - xa, 2), zona.height()), c)
        if self._media is not None:
            xm = zona.left() + (self._media - lo) / (hi - lo) * zona.width()
            p.setPen(QPen(QColor("#FFD166"), 2, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(xm, zona.top()), QPointF(xm, zona.bottom()))
