"""Barras divergentes de la variación porcentual (V = (Xalt − Xbase) / Xbase · 100)."""
from typing import Optional, Sequence

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from .. import theme


class BarraVariacion:
    def __init__(self, etiqueta: str, valor: Optional[float], color: str):
        self.etiqueta, self.valor, self.color = etiqueta, valor, color


class VariationChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._barras: list[BarraVariacion] = []
        self.setMinimumHeight(190)

    def set_barras(self, barras: Sequence[BarraVariacion]) -> None:
        self._barras = list(barras)
        self.setMinimumHeight(60 + 34 * max(len(self._barras), 1))
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if not self._barras:
            p.setPen(QColor(theme.TENUE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Ejecute una comparación para ver las variaciones.")
            return
        izq, der, arriba = 290, 80, 12
        zona = w - izq - der
        vals = [abs(b.valor) for b in self._barras if b.valor is not None]
        tope = max(vals + [1.0])
        cero = izq + zona / 2
        fila = (h - arriba - 8) / len(self._barras)
        p.setPen(QPen(QColor(theme.BORDE), 1, Qt.PenStyle.DashLine))
        p.drawLine(int(cero), int(arriba), int(cero), int(h - 8))
        fuente = QFont("Segoe UI", 9)
        p.setFont(fuente)
        for i, b in enumerate(self._barras):
            y = arriba + i * fila
            p.setPen(QColor(theme.TEXTO))
            p.drawText(QRectF(6, y, izq - 14, fila), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, b.etiqueta)
            if b.valor is None:
                p.setPen(QColor(theme.TENUE))
                p.drawText(QRectF(cero + 8, y, 200, fila), Qt.AlignmentFlag.AlignVCenter, "n/d (sin datos)")
                continue
            largo = abs(b.valor) / tope * (zona / 2 - 4)
            x = cero if b.valor >= 0 else cero - largo
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(b.color))
            p.drawRoundedRect(QRectF(x, y + fila * 0.22, max(largo, 2), fila * 0.56), 3, 3)
            p.setPen(QColor(theme.TEXTO))
            texto = f"{b.valor:+.1f} %"
            if b.valor >= 0:
                p.drawText(QRectF(cero + largo + 6, y, 80, fila), Qt.AlignmentFlag.AlignVCenter, texto)
            else:
                p.drawText(QRectF(cero - largo - 86, y, 80, fila), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, texto)
