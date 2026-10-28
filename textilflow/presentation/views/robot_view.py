from typing import Sequence

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import PageView
from ..widgets.crud_panel import CrudPanel


class RobotView(PageView):
    evaluar_solicitado = pyqtSignal(int)

    def __init__(self, origenes: list[tuple]):
        super().__init__("Diseño conceptual del robot",
                         "Registre parámetros medibles del robot (AMR) y evalúe su compatibilidad preliminar con el taller. "
                         "La factibilidad por ancho es geométrica, no una certificación de seguridad.",
                         theme.TURQUESA)
        campos = [
            CampoSpec("nombre", "Nombre *", placeholder="Ej.: AMR Conceptual 01"),
            CampoSpec("capacidad_kg", "Capacidad carga (kg) *", "float", 0.1, 100_000, 2, 50.0),
            CampoSpec("velocidad_ms", "Velocidad (m/s) *", "float", 0.01, 100, 3, 0.7),
            CampoSpec("ancho_m", "Ancho robot (m) *", "float", 0.01, 100, 3, 0.75),
            CampoSpec("radio_giro_m", "Radio de giro (m)", "float", 0, 100, 3, 0.9),
            CampoSpec("origen_datos", "Origen de datos", "combo"),
        ]
        self.panel = CrudPanel("Nuevo perfil de robot", "Perfiles de robot registrados", campos,
                               ["ID", "Nombre", "Cap. kg", "Vel. m/s", "Ancho m", "Radio giro m", "Origen"],
                               theme.TURQUESA, estirar=1)
        self.panel.set_opciones("origen_datos", origenes)
        self.cuerpo.addWidget(self.panel, 1)

        caja = QFrame()
        caja.setObjectName("tarjeta")
        cl = QVBoxLayout(caja)
        t = QLabel("Evaluación preliminar robot ↔ taller activo")
        t.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {theme.TURQUESA}; padding-left: 8px;")
        cl.addWidget(t)
        fila = QHBoxLayout()
        fila.addWidget(QLabel("Robot:"))
        self.combo = QComboBox()
        fila.addWidget(self.combo, 1)
        self.boton = QPushButton("Evaluar compatibilidad")
        self.boton.setObjectName("primario")
        fila.addWidget(self.boton)
        cl.addLayout(fila)
        self.resultado = QLabel("Seleccione un robot para iniciar la evaluación.")
        self.resultado.setWordWrap(True)
        cl.addWidget(self.resultado)
        self.cuerpo.addWidget(caja)
        self.cuerpo.addWidget(self.estado)
        self.boton.clicked.connect(self._emitir)

    def set_robots(self, opciones: Sequence[tuple]) -> None:
        previo = self.combo.currentData()
        self.combo.clear()
        for id_, etiqueta in opciones:
            self.combo.addItem(etiqueta, id_)
        self.combo.setCurrentIndex(max(self.combo.findData(previo), 0))

    def mostrar_evaluacion(self, html: str) -> None:
        self.resultado.setText(html)

    def _emitir(self) -> None:
        if self.combo.currentData() is not None:
            self.evaluar_solicitado.emit(int(self.combo.currentData()))
