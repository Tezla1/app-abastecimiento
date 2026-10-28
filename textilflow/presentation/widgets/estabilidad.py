from typing import Sequence

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QWidget

from .. import theme

ALTO_FILA = 54


class Estabilidad(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filas: list[tuple] = []
        self._mensaje = ""
        self.setMinimumHeight(160)

    def set_datos(self, filas: Sequence[tuple], mensaje: str = "") -> None:
        self._filas, self._mensaje = list(filas), mensaje
        self.setMinimumHeight(70 + ALTO_FILA * len(self._filas))
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        if not self._filas:
            p.setPen(QColor(theme.TENUE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Ejecute las réplicas para ver qué tan estable es el resultado.")
            return
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(theme.TEXTO))
        p.drawText(QRectF(8, 2, w - 16, 20), Qt.AlignmentFlag.AlignVCenter, "¿Qué tan estable es el resultado?")
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor(theme.TENUE))
        p.drawText(QRectF(8, 24, w - 16, 36), Qt.TextFlag.TextWordWrap, self._mensaje)
        # las filas arrancan debajo de la explicación
        y = 66
        for nombre, valor, rango, nivel, color, fraccion in self._filas:
            p.setPen(QColor(theme.TEXTO))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(QRectF(8, y, w * 0.55, 18), Qt.AlignmentFlag.AlignVCenter, nombre)
            fb = QFont("Segoe UI", 10)
            fb.setBold(True)
            p.setFont(fb)
            p.drawText(QRectF(w * 0.55, y, w * 0.45 - 8, 18), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, valor)
            pista = QRectF(8, y + 23, w - 16, 7)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.PANEL_2))
            p.drawRoundedRect(pista, 3.5, 3.5)
            p.setBrush(QColor(color))
            p.drawRoundedRect(QRectF(pista.left(), pista.top(), max(pista.width() * fraccion, 7), pista.height()), 3.5, 3.5)
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor(color))
            p.drawText(QRectF(8, y + 32, w * 0.4, 14), Qt.AlignmentFlag.AlignVCenter, nivel)
            p.setPen(QColor(theme.TENUE))
            p.drawText(QRectF(w * 0.4, y + 32, w * 0.6 - 8, 14), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, rango)
            y += ALTO_FILA
