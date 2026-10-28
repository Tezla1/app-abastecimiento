# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Página de Validación integral.

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton

from .. import theme
from ..widgets.common import TablaDatos, TarjetaKpi, VistaPagina
from ..widgets.adaptable import FlujoLayout


class ValidacionView(VistaPagina):
    ejecutar_solicitado = pyqtSignal()

    def __init__(self):
        super().__init__("Validación integral",
                         "Verificación transversal del proyecto antes de declarar aptitud para simulación, comparación y reporte.",
                         theme.DORADO)
        fila = FlujoLayout()
        self.k_pass = TarjetaKpi("APROBADO", "#1B7A57")
        self.k_warn = TarjetaKpi("ADVERTENCIA", "#B8701A")
        self.k_fail = TarjetaKpi("FALLA", "#8C3A44")
        for k in (self.k_pass, self.k_warn, self.k_fail):
            fila.addWidget(k)
        self.boton = QPushButton("Ejecutar validación integral")
        self.boton.setObjectName("primario")
        fila.addWidget(self.boton)
        self.cuerpo.addLayout(fila)
        self.veredicto = QLabel("Pulse «Ejecutar validación integral».")
        self.veredicto.setWordWrap(True)
        self.cuerpo.addWidget(self.veredicto)
        self.tabla = TablaDatos(["Estado", "Código", "Área", "Hallazgo", "Corregir en"], estirar=3)
        self.cuerpo.addWidget(self.tabla, 1)
        criterio = QLabel("Criterio científico: se distinguen integridad de datos, factibilidad geométrica, "
                          "comparabilidad y datos aún no validados. Una ADVERTENCIA no es una FALLA, pero debe documentarse.")
        criterio.setObjectName("tenue")
        criterio.setWordWrap(True)
        self.cuerpo.addWidget(criterio)
        self.boton.clicked.connect(self.ejecutar_solicitado.emit)

    def mostrar(self, n_pass: int, n_warn: int, n_fail: int, veredicto: str, filas: list, colores: list) -> None:
        self.k_pass.set_valor(str(n_pass))
        self.k_warn.set_valor(str(n_warn))
        self.k_fail.set_valor(str(n_fail))
        self.veredicto.setText(veredicto)
        self.tabla.set_filas(filas, colores=colores)
