# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Rejilla de tarjetas de la comparación: el valor de cada indicador en S0 y S1 y su variación porcentual.

from typing import Sequence

from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from .. import theme

COLUMNAS = 3


class TarjetasComparacion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rejilla = QGridLayout(self)
        self._rejilla.setContentsMargins(0, 0, 0, 0)
        self._rejilla.setSpacing(10)
        self.limpiar()

    def limpiar(self) -> None:
        while self._rejilla.count():
            w = self._rejilla.takeAt(0).widget()
            if w:
                w.deleteLater()
        vacio = QLabel("Ejecute una comparación para ver qué mejora y qué empeora.")
        vacio.setObjectName("tenue")
        self._rejilla.addWidget(vacio, 0, 0)

    def set_tarjetas(self, tarjetas: Sequence[tuple]) -> None:
        while self._rejilla.count():
            w = self._rejilla.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i, (nombre, antes, despues, cambio, color, veredicto) in enumerate(tarjetas):
            caja = QFrame()
            caja.setObjectName("tarjeta")
            caja.setStyleSheet(f"QFrame#tarjeta {{ border-left: 5px solid {color}; }}")
            lay = QVBoxLayout(caja)
            lay.setSpacing(2)
            t = QLabel(nombre)
            t.setWordWrap(True)
            t.setStyleSheet("font-weight: 600;")
            c = QLabel(f"{veredicto}  {cambio}")
            c.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {color};")
            d = QLabel(f"{antes}  →  {despues}")
            d.setObjectName("tenue")
            for w in (t, c, d):
                lay.addWidget(w)
            self._rejilla.addWidget(caja, i // COLUMNAS, i % COLUMNAS)
        for j in range(COLUMNAS):
            self._rejilla.setColumnStretch(j, 1)
