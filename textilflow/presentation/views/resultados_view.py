from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QPlainTextEdit, QPushButton

from .. import theme
from ..widgets.common import PageView
from ..widgets.par_escenarios import ParEscenariosBar


class ResultadosView(PageView):
    exportar_solicitado = pyqtSignal(int, int, str, str)

    def __init__(self):
        super().__init__("Resultados y reportes",
                         "Informe de la comparación entre escenarios, listo para exportar a Excel o CSV.",
                         theme.NARANJA)
        self.barra = ParEscenariosBar("Generar informe")
        self.cuerpo.addWidget(self.barra)
        self.texto = QPlainTextEdit()
        self.texto.setReadOnly(True)
        self.texto.setPlaceholderText("Aquí aparecerá el informe de la comparación.")
        self.cuerpo.addWidget(self.texto, 1)
        fila = QHBoxLayout()
        fila.addStretch(1)
        self.btn_xlsx = QPushButton("Exportar Excel (.xlsx)")
        self.btn_csv = QPushButton("Exportar CSV")
        self.btn_xlsx.setObjectName("primario")
        fila.addWidget(self.btn_csv)
        fila.addWidget(self.btn_xlsx)
        self.cuerpo.addLayout(fila)
        self.cuerpo.addWidget(self.estado)
        self.btn_xlsx.clicked.connect(lambda: self._exportar("xlsx"))
        self.btn_csv.clicked.connect(lambda: self._exportar("csv"))

    def mostrar_informe(self, texto: str) -> None:
        self.texto.setPlainText(texto)

    def _exportar(self, formato: str) -> None:
        b, a = self.barra.base.currentData(), self.barra.alt.currentData()
        if b is None or a is None:
            self.error("Seleccione los dos escenarios.")
            return
        filtro = "Excel (*.xlsx)" if formato == "xlsx" else "CSV (*.csv)"
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar reporte", f"comparacion.{formato}", filtro)
        if ruta:
            if not ruta.lower().endswith("." + formato):
                ruta += "." + formato
            self.exportar_solicitado.emit(int(b), int(a), ruta, formato)
