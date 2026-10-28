from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

from .. import theme
from ..textos import FORMULA_VARIACION
from ..widgets.common import DataTable, PageView
from ..widgets.line_chart import LineChart
from ..widgets.par_escenarios import ParEscenariosBar
from ..widgets.tarjetas_comparacion import TarjetasComparacion


class ComparacionView(PageView):
    def __init__(self):
        super().__init__("Comparación experimental",
                         f"Control experimental y trazabilidad: indicadores de dos escenarios del mismo taller. {FORMULA_VARIACION}",
                         theme.MORADO)
        self.barra = ParEscenariosBar("Comparar S0 vs S1")
        self.cuerpo.addWidget(self.barra)
        self.veredicto = QLabel("Elija dos escenarios simulados y pulse «Comparar».")
        self.veredicto.setWordWrap(True)
        self.cuerpo.addWidget(self.veredicto)
        t = QLabel("¿Qué mejora y qué empeora con el escenario alternativo?")
        t.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.cuerpo.addWidget(t)
        self.tarjetas = TarjetasComparacion()
        self.cuerpo.addWidget(self.tarjetas)

        self.tabla = DataTable(["Indicador", "Base", "Alternativo", "Variación (%)"], estirar=0)
        self.tabla.setFixedHeight(190)
        self.cuerpo.addWidget(self.tabla)
        self.tabla_proceso = DataTable(["Indicador del proceso completo", "Base", "Alternativo", "Variación (%)"], estirar=0)
        self.tabla_proceso.setFixedHeight(190)
        self.cuerpo.addWidget(self.tabla_proceso)
        caja0 = QFrame()
        caja0.setObjectName("tarjeta")
        c0 = QVBoxLayout(caja0)
        self.g_avance = LineChart("Lotes completados en el tiempo", "min")
        c0.addWidget(self.g_avance)
        self.cuerpo.addWidget(caja0, 1)

    def mostrar(self, veredicto: str, filas: list, tarjetas: list, filas_proceso: list = (), avance=None) -> None:
        self.veredicto.setText(veredicto)
        self.tabla.set_filas(filas)
        self.tabla_proceso.set_filas(list(filas_proceso))
        if avance:
            self.g_avance.set_datos(*avance)
        self.tarjetas.set_tarjetas(tarjetas)
