from typing import Sequence

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .. import theme
from ..textos import FORMULA_VARIACION
from ..widgets.common import TablaDatos, VistaPagina
from ..widgets.adaptable import FilaAdaptable


class ModeloView(VistaPagina):
    calcular_solicitado = pyqtSignal(int)

    def __init__(self):
        super().__init__("Modelo matemático",
                         "Parte matemática: indicadores de calculos.py sobre los traslados del escenario y carga ofrecida analítica (ρ) de cada área.",
                         theme.VERDE)
        barra = QFrame()
        barra.setObjectName("tarjeta")
        bl = FilaAdaptable(barra)
        bl.addWidget(QLabel("Escenario:"))
        self.combo = QComboBox()
        bl.addWidget(self.combo, 1)
        self.boton = QPushButton("Calcular indicadores")
        self.boton.setObjectName("primario")
        bl.addWidget(self.boton)
        self.cuerpo.addWidget(barra)

        self.resumen = QLabel("Seleccione un escenario y calcule sus indicadores.")
        self.resumen.setWordWrap(True)
        self.cuerpo.addWidget(self.resumen)

        self.tabla_ind = TablaDatos(["Indicador", "Valor", "Fórmula"], estirar=2)
        self.tabla_ind.setFixedHeight(220)
        self.cuerpo.addWidget(self.tabla_ind)
        sub0 = QLabel("Carga ofrecida analítica  ρ = Σ(unidades × min/unidad × factor) / (puestos × turno)")
        sub0.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.cuerpo.addWidget(sub0)
        self.tabla_rho = TablaDatos(["Área", "Puestos", "Trabajo ofrecido (min)", "ρ %", "Lectura"], estirar=4)
        self.tabla_rho.setFixedHeight(190)
        self.cuerpo.addWidget(self.tabla_rho)
        sub = QLabel("Traslados del escenario (cada lote que se mueve entre dos áreas)")
        sub.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.cuerpo.addWidget(sub)
        self.tabla_reg = TablaDatos(["Pedido", "Lote", "Desde → Hacia", "Atendido", "Espera (min)", "Recorrido (min)",
                                    "Distancia (m)", "Viajes", "Detalle"], estirar=8)
        self.cuerpo.addWidget(self.tabla_reg, 1)
        nota = QLabel(f"Comparación entre escenarios: {FORMULA_VARIACION}  (ver «Comparación experimental»).")
        nota.setObjectName("tenue")
        self.cuerpo.addWidget(nota)
        self.boton.clicked.connect(self._emitir)

    def set_escenarios(self, opciones: Sequence[tuple]) -> None:
        previo = self.combo.currentData()
        self.combo.clear()
        for id_, etiqueta in opciones:
            self.combo.addItem(etiqueta, id_)
        i = self.combo.findData(previo)
        self.combo.setCurrentIndex(max(i, 0))

    def mostrar(self, resumen: str, filas_ind: list, filas_reg: list, filas_rho: list = (), colores_rho: list = None) -> None:
        self.resumen.setText(resumen)
        self.tabla_ind.set_filas(filas_ind)
        self.tabla_rho.set_filas(list(filas_rho), colores=colores_rho)
        self.tabla_reg.set_filas(filas_reg)

    def _emitir(self) -> None:
        if self.combo.currentData() is not None:
            self.calcular_solicitado.emit(int(self.combo.currentData()))
