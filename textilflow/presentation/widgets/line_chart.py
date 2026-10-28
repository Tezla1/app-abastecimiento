"""Gráfico de líneas simple con cuadrícula, leyenda y marcador de instante (para animaciones)."""
from typing import Optional, Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from .. import theme


class LineChart(QWidget):
    def __init__(self, titulo: str = "", etiqueta_x: str = "min", etiqueta_y: str = "", parent=None):
        super().__init__(parent)
        self.titulo, self.etiqueta_x, self.etiqueta_y = titulo, etiqueta_x, etiqueta_y
        self._x: list[float] = []
        self._series: list[tuple] = []
        self._marca: Optional[float] = None
        self._escalonado = False
        self.setMinimumHeight(180)

    def set_datos(self, x: Sequence[float], series: Sequence[tuple], escalonado: bool = False) -> None:
        """series: [(nombre, color, valores)] con la misma longitud que x."""
        self._x, self._series, self._escalonado = list(x), list(series), escalonado
        self.update()

    def set_marca(self, x: Optional[float]) -> None:
        self._marca = x
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setFont(QFont("Segoe UI", 9))
        if self.titulo:
            p.setPen(QColor(theme.TEXTO))
            f = QFont("Segoe UI", 10)
            f.setBold(True)
            p.setFont(f)
            p.drawText(QRectF(8, 2, w - 16, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.titulo)
            p.setFont(QFont("Segoe UI", 9))
        izq, der, arr, aba = 46, 14, 28, 28
        zona = QRectF(izq, arr, max(w - izq - der, 10), max(h - arr - aba, 10))
        if not self._x or not self._series:
            p.setPen(QColor(theme.TENUE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin datos todavía.")
            return
        x0, x1 = self._x[0], self._x[-1] if self._x[-1] > self._x[0] else self._x[0] + 1
        vmax = max((max(v) for _, _, v in self._series if v), default=1.0)
        vmax = max(vmax, 1e-9)
        tope = self._redondear(vmax)
        # cuadrícula
        for i in range(5):
            y = zona.bottom() - zona.height() * i / 4
            p.setPen(QPen(QColor(theme.BORDE), 1, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(zona.left(), y), QPointF(zona.right(), y))
            p.setPen(QColor(theme.TENUE))
            p.drawText(QRectF(0, y - 8, izq - 6, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       f"{tope * i / 4:g}")
        for i in range(6):
            xv = x0 + (x1 - x0) * i / 5
            xp = zona.left() + zona.width() * i / 5
            p.setPen(QColor(theme.TENUE))
            p.drawText(QRectF(xp - 30, zona.bottom() + 4, 60, 16), Qt.AlignmentFlag.AlignHCenter, f"{xv:.0f}")
        p.drawText(QRectF(zona.left(), h - 16, zona.width(), 14), Qt.AlignmentFlag.AlignRight, self.etiqueta_x)
        if self.etiqueta_y:
            p.drawText(QRectF(2, 6, izq + 30, 14), Qt.AlignmentFlag.AlignLeft, "")
        # series
        for nombre, color, vals in self._series:
            ruta = QPainterPath()
            previo = None
            for xv, yv in zip(self._x, vals):
                px = zona.left() + (xv - x0) / (x1 - x0) * zona.width()
                py = zona.bottom() - min(yv, tope) / tope * zona.height()
                if previo is None:
                    ruta.moveTo(px, py)
                else:
                    if self._escalonado:
                        ruta.lineTo(px, previo)
                    ruta.lineTo(px, py)
                previo = py
            p.setPen(QPen(QColor(color), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(ruta)
        # marcador de instante
        if self._marca is not None and x0 <= self._marca <= x1:
            xp = zona.left() + (self._marca - x0) / (x1 - x0) * zona.width()
            p.setPen(QPen(QColor("#FFD166"), 1.5, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(xp, zona.top()), QPointF(xp, zona.bottom()))
        # leyenda
        x = zona.right()
        for nombre, color, _ in reversed(self._series):
            ancho = p.fontMetrics().horizontalAdvance(nombre) + 26
            x -= ancho
            p.setPen(QPen(QColor(color), 3))
            p.drawLine(QPointF(x, 12), QPointF(x + 14, 12))
            p.setPen(QColor(theme.TEXTO))
            p.drawText(QRectF(x + 18, 4, ancho - 18, 16), Qt.AlignmentFlag.AlignVCenter, nombre)

    @staticmethod
    def _redondear(v: float) -> float:
        import math
        if v <= 0:
            return 1.0
        e = 10 ** math.floor(math.log10(v))
        for m in (1, 2, 2.5, 5, 10):
            if v <= m * e:
                return m * e
        return 10 * e
