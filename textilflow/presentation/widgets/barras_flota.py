# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Barras de ocupación de la flota para cada cantidad de recursos probada; el color indica si sobran equipos, la carga es adecuada o está saturada.

from typing import Sequence

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from .. import theme

ALTO_FILA = 46

LEYENDA = [("#4F8FE8", "Equipos de sobra"), (theme.VERDE, "Carga adecuada"),
           (theme.NARANJA, "Muy justo"), (theme.ROJO, "Saturado")]


def color_ocupacion(pct: float, objetivo: float) -> str:
    if pct > 90:
        return theme.ROJO
    if pct > objetivo:
        return theme.NARANJA
    if pct >= objetivo * 0.4:
        return theme.VERDE
    return "#4F8FE8"


class BarrasFlota(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filas: list[tuple] = []
        self._objetivo = 75.0
        self.setMinimumHeight(200)

    def set_datos(self, filas: Sequence[tuple], objetivo: float) -> None:
        self._filas, self._objetivo = list(filas), objetivo
        self.setMinimumHeight(86 + ALTO_FILA * len(self._filas))
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(theme.TEXTO))
        p.drawText(QRectF(8, 2, w - 16, 20), Qt.AlignmentFlag.AlignVCenter, "¿Cuánto trabaja cada equipo de transporte?")
        if not self._filas:
            p.setFont(QFont("Segoe UI", 9))
            p.setPen(QColor(theme.TENUE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Pulse «Analizar requerimientos» para ver la comparación.")
            return
        x = 8
        p.setFont(QFont("Segoe UI", 8))
        for color, texto in LEYENDA:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(color))
            p.drawRoundedRect(QRectF(x, 31, 10, 10), 2, 2)
            p.setPen(QColor(theme.TENUE))
            ancho = p.fontMetrics().horizontalAdvance(texto)
            p.drawText(QRectF(x + 14, 28, ancho + 6, 16), Qt.AlignmentFlag.AlignVCenter, texto)
            x += ancho + 34
        izq, der, arriba = 92, 170, 58
        zona = max(w - izq - der, 40)
        for i, (etiqueta, pct, texto, recomendado) in enumerate(self._filas):
            y = arriba + i * ALTO_FILA
            p.setFont(QFont("Segoe UI", 10))
            p.setPen(QColor(theme.TEXTO))
            p.drawText(QRectF(8, y, izq - 14, 26), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, etiqueta)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.PANEL_2))
            p.drawRoundedRect(QRectF(izq, y + 3, zona, 20), 4, 4)
            largo = zona * min(pct, 100) / 100
            p.setBrush(QColor(color_ocupacion(pct, self._objetivo)))
            p.drawRoundedRect(QRectF(izq, y + 3, max(largo, 4), 20), 4, 4)
            p.setPen(QColor("white"))
            fb = QFont("Segoe UI", 9)
            fb.setBold(True)
            p.setFont(fb)
            p.drawText(QRectF(izq + 8, y + 3, zona, 20), Qt.AlignmentFlag.AlignVCenter, f"{pct:.0f} % ocupado")
            p.setFont(QFont("Segoe UI", 9))
            p.setPen(QColor(theme.TENUE))
            p.drawText(QRectF(izq + zona + 10, y, der - 10, 26), Qt.AlignmentFlag.AlignVCenter, texto)
            if recomendado:
                p.setPen(QColor(theme.DORADO))
                p.setFont(fb)
                p.drawText(QRectF(izq, y + 25, zona, 16), Qt.AlignmentFlag.AlignVCenter, "★ Recomendado")
        xo = izq + zona * self._objetivo / 100
        p.setPen(QPen(QColor(theme.DORADO), 1.5, Qt.PenStyle.DashLine))
        fin = arriba + ALTO_FILA * len(self._filas)
        p.drawLine(int(xo), arriba - 4, int(xo), fin)
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QRectF(xo - 60, fin + 2, 120, 14), Qt.AlignmentFlag.AlignHCenter, f"meta {self._objetivo:.0f} %")
