# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Barra con dos listas para elegir el escenario base y el alternativo, y el botón que ejecuta la comparación.

from typing import Sequence

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QPushButton


class BarraParEscenarios(QFrame):
    ejecutar = pyqtSignal(int, int)

    def __init__(self, texto_boton: str, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        g = QGridLayout(self)
        self.base = QComboBox()
        self.alt = QComboBox()
        self.boton = QPushButton(texto_boton)
        self.boton.setObjectName("primario")
        g.addWidget(QLabel("Base (S0):"), 0, 0)
        g.addWidget(self.base, 0, 1)
        g.addWidget(QLabel("Alternativo (S1):"), 0, 2)
        g.addWidget(self.alt, 0, 3)
        g.addWidget(self.boton, 0, 4)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(3, 1)
        self.boton.clicked.connect(self._emitir)

    def set_escenarios(self, opciones: Sequence[tuple]) -> None:
        previos = (self.base.currentData(), self.alt.currentData())
        for combo, previo, defecto in ((self.base, previos[0], 0), (self.alt, previos[1], 1)):
            combo.blockSignals(True)
            combo.clear()
            for id_, etiqueta in opciones:
                combo.addItem(etiqueta, id_)
            i = combo.findData(previo) if previo is not None else -1
            if i < 0:
                i = min(defecto, combo.count() - 1)
            combo.setCurrentIndex(i)
            combo.blockSignals(False)

    def _emitir(self) -> None:
        b, a = self.base.currentData(), self.alt.currentData()
        if b is None or a is None:
            return
        self.ejecutar.emit(int(b), int(a))
