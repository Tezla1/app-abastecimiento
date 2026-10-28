from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import DataTable, PageView
from ..widgets.crud_panel import CrudPanel
from ..widgets.mapa_operativo import MapaOperativo


class ContingenciasView(PageView):
    exportar_solicitado = pyqtSignal(str, int)
    ruta_elegida = pyqtSignal(int)

    def __init__(self, motivos: list[tuple]):
        super().__init__("Contingencias y cierres",
                         "Cierre un área cuando falle una máquina, falte personal o haya mantenimiento. El sistema recalcula "
                         "rutas y simulaciones solo, y le muestra aquí qué área quedó afectada y por dónde se desvía el trabajo.",
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
        self.panel.setMinimumHeight(350)
        self.panel.setMaximumHeight(370)
        self.panel.widget("hasta_min").setToolTip("0 = el área no reabre durante el turno")
        self.cuerpo.addWidget(self.panel)
        self.cuerpo.addWidget(self.estado)

        caja = QFrame()
        caja.setObjectName("tarjeta")
        cl = QVBoxLayout(caja)
        fila = QHBoxLayout()
        t = QLabel("Área afectada y ruta de respaldo")
        t.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {theme.ROJO}; padding-left: 8px;")
        fila.addWidget(t)
        fila.addStretch(1)
        fila.addWidget(QLabel("Escenario:"))
        self.combo_escenario = QComboBox()
        self.combo_escenario.setMinimumWidth(260)
        fila.addWidget(self.combo_escenario)
        self.btn_informe = QPushButton("Generar informe (Excel)")
        self.btn_informe.setObjectName("primario")
        fila.addWidget(self.btn_informe)
        cl.addLayout(fila)

        cuerpo = QHBoxLayout()
        self.mapa = MapaOperativo()
        self.mapa.mostrar_distancias = False
        self.mapa.setMinimumHeight(260)
        cuerpo.addWidget(self.mapa, 3)
        der = QVBoxLayout()
        self.tabla_rutas = DataTable(["Prenda · rama", "Ruta de respaldo"], estirar=1)
        der.addWidget(self.tabla_rutas, 1)
        self.leyenda = QLabel("✕ área cerrada · línea amarilla: ruta de respaldo · naranja punteada: ruta normal bloqueada")
        self.leyenda.setObjectName("tenue")
        self.leyenda.setWordWrap(True)
        der.addWidget(self.leyenda)
        cuerpo.addLayout(der, 2)
        cl.addLayout(cuerpo, 1)
        self.cuerpo.addWidget(caja, 1)

        self.btn_informe.clicked.connect(self._pedir_archivo)
        self.tabla_rutas.fila_seleccionada.connect(lambda i: i is not None and self.ruta_elegida.emit(int(i)))

    def set_escenarios(self, opciones: list[tuple]) -> None:
        actual = self.combo_escenario.currentData()
        self.combo_escenario.clear()
        for id_, nombre in opciones:
            self.combo_escenario.addItem(nombre, id_)
        i = self.combo_escenario.findData(actual)
        if i >= 0:
            self.combo_escenario.setCurrentIndex(i)

    def _pedir_archivo(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Generar informe", "contingencias.xlsx", "Excel (*.xlsx)")
        if ruta:
            self.exportar_solicitado.emit(ruta if ruta.lower().endswith(".xlsx") else ruta + ".xlsx",
                                          self.combo_escenario.currentData() or 0)
