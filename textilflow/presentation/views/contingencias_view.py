from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import PageView
from ..widgets.crud_panel import CrudPanel


class ContingenciasView(PageView):
    informe_solicitado = pyqtSignal(int)
    exportar_solicitado = pyqtSignal(str)

    def __init__(self, motivos: list[tuple]):
        super().__init__("Contingencias y cierres",
                         "Cierre un área cuando falle una máquina, falte personal o haya mantenimiento. El sistema recalcula "
                         "rutas y simulaciones solo, y redacta el informe de por qué se cerró y qué cambió.",
                         theme.ROJO)
        campos = [
            CampoSpec("codigo", "Área a cerrar *", "combo"),
            CampoSpec("motivo", "Motivo *", "combo"),
            CampoSpec("detalle", "¿Qué pasó?", "multiline"),
            CampoSpec("desde_min", "Desde el minuto", "float", 0, 100_000, 1, 0.0),
            CampoSpec("hasta_min", "Reabre en el minuto", "float", 0, 100_000, 1, 0.0),
            CampoSpec("bloquea_paso", "Bloquea el paso", "check", defecto=True),
            CampoSpec("vigente", "Cierre activo", "check", defecto=True),
        ]
        self.panel = CrudPanel("Registrar cierre", "Cierres registrados del taller", campos,
                               ["ID", "Área", "Motivo", "Desde", "Reapertura", "Estado"], theme.ROJO, 420, estirar=2)
        self.panel.set_opciones("motivo", motivos)
        self.panel.setMinimumHeight(320)
        self.panel.setMaximumHeight(330)
        self.panel.widget("hasta_min").setToolTip("0 = el área no reabre durante el turno")
        self.cuerpo.addWidget(self.panel)
        self.cuerpo.addWidget(self.estado)

        caja = QFrame()
        caja.setObjectName("tarjeta")
        cl = QVBoxLayout(caja)
        fila = QHBoxLayout()
        t = QLabel("Informe de contingencia")
        t.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {theme.ROJO}; padding-left: 8px;")
        fila.addWidget(t)
        fila.addStretch(1)
        fila.addWidget(QLabel("Escenario:"))
        self.combo_escenario = QComboBox()
        self.combo_escenario.setMinimumWidth(260)
        fila.addWidget(self.combo_escenario)
        self.btn_informe = QPushButton("Generar informe")
        self.btn_informe.setObjectName("primario")
        self.btn_exportar = QPushButton("Guardar como HTML…")
        self.btn_exportar.setEnabled(False)
        fila.addWidget(self.btn_informe)
        fila.addWidget(self.btn_exportar)
        cl.addLayout(fila)
        self.navegador = QTextBrowser()
        self.navegador.setStyleSheet(f"background: {theme.PANEL}; border: 1px solid {theme.BORDE}; border-radius: 8px;")
        self.navegador.setHtml(f"<p style='color:{theme.TENUE}'>Registre un cierre y el informe aparece aquí.</p>")
        cl.addWidget(self.navegador, 1)
        self.cuerpo.addWidget(caja, 1)

        self.btn_informe.clicked.connect(lambda: self.informe_solicitado.emit(self.combo_escenario.currentData() or 0))
        self.btn_exportar.clicked.connect(self._exportar)

    def set_escenarios(self, opciones: list[tuple]) -> None:
        actual = self.combo_escenario.currentData()
        self.combo_escenario.clear()
        for id_, nombre in opciones:
            self.combo_escenario.addItem(nombre, id_)
        i = self.combo_escenario.findData(actual)
        if i >= 0:
            self.combo_escenario.setCurrentIndex(i)

    def mostrar_informe(self, html: str) -> None:
        self.navegador.setHtml(html)
        self.btn_exportar.setEnabled(True)

    def _exportar(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar informe", "informe_contingencia.html", "Página web (*.html)")
        if ruta:
            self.exportar_solicitado.emit(ruta)
