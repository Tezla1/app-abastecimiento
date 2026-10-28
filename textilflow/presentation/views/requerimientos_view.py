from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                             QTabWidget, QVBoxLayout, QWidget)

from .. import theme
from ..widgets.common import DataTable, KpiCard, PageView
from ..widgets.barras_flota import BarrasFlota


class RequerimientosView(PageView):
    analizar_solicitado = pyqtSignal(int, int)
    guardar_parametro = pyqtSignal(str, float)
    restaurar_parametros = pyqtSignal()
    parametro_elegido = pyqtSignal(str)

    def __init__(self):
        super().__init__("Requerimientos y normativas",
                         "Qué componentes son críticos, qué distancias se recorren, cuántos equipos y cuántos viajes hacen falta "
                         "y qué normas aplican. Todo se recalcula con la simulación del escenario elegido.",
                         theme.DORADO)
        barra = QFrame(); barra.setObjectName("tarjeta")
        bl = QHBoxLayout(barra)
        bl.addWidget(QLabel("Escenario de análisis:"))
        self.combo = QComboBox(); self.combo.setMinimumWidth(260)
        bl.addWidget(self.combo)
        bl.addWidget(QLabel("Probar flotas de 1 a:"))
        self.n_max = QSpinBox(); self.n_max.setRange(2, 12); self.n_max.setValue(6)
        bl.addWidget(self.n_max)
        self.btn = QPushButton("Analizar requerimientos")
        self.btn.setObjectName("primario")
        bl.addStretch(1)
        bl.addWidget(self.btn)
        self.cuerpo.addWidget(barra)
        self.resumen = QLabel("Elija un escenario y pulse «Analizar requerimientos».")
        self.resumen.setWordWrap(True)
        self.cuerpo.addWidget(self.resumen)

        self.tabs = QTabWidget()
        self.t_criticos = DataTable(["Severidad", "Tipo", "Elemento", "Motivo"], estirar=3)
        self.tabs.addTab(self.t_criticos, "Componentes críticos")
        d = QWidget(); dl = QVBoxLayout(d); dl.setContentsMargins(0, 0, 0, 0)
        self.t_ramas = DataTable(["Prenda", "Rama", "%", "Camino físico", "Distancia m", "Transporte min"], estirar=3)
        dl.addWidget(self.t_ramas, 2)
        self.lbl_recorridos = QLabel("")
        self.lbl_recorridos.setWordWrap(True)
        dl.addWidget(self.lbl_recorridos)
        self.t_recursos = DataTable(["Recurso", "Viajes cargados", "Distancia m", "Ocupado min"], estirar=None)
        dl.addWidget(self.t_recursos, 1)
        self.tabs.addTab(d, "Distancias y recorridos")
        e = QWidget(); el = QVBoxLayout(e); el.setContentsMargins(0, 0, 0, 0)
        fila = QHBoxLayout()
        self.k_reco = KpiCard("Equipos recomendados", "#1B7A57")
        self.k_anal = KpiCard("Estimación analítica", "#1F4E9E")
        self.k_viajes = KpiCard("Viajes cargados del turno", "#6B43A8")
        self.k_dist = KpiCard("Distancia total del turno", "#B8701A")
        for k in (self.k_reco, self.k_anal, self.k_viajes, self.k_dist):
            fila.addWidget(k)
        el.addLayout(fila)
        medio = QHBoxLayout()
        self.t_barrido = DataTable(["Equipos", "Util. %", "Espera min", "Lotes ok %", "Lead time", "Cierre min",
                                    "A tiempo %", "Cumple"], estirar=None)
        medio.addWidget(self.t_barrido, 3)
        caja = QFrame(); caja.setObjectName("tarjeta")
        cl = QVBoxLayout(caja)
        self.g_barrido = BarrasFlota()
        cl.addWidget(self.g_barrido)
        medio.addWidget(caja, 2)
        el.addLayout(medio, 2)
        self.t_viajes = DataTable(["Prenda", "kg/u", "Lote (u)", "Lote kg", "u/viaje", "Viajes por traslado",
                                   "Lotes", "Traslados/lote", "Viajes estimados"], estirar=None)
        el.addWidget(self.t_viajes, 1)
        self.notas = QLabel("")
        self.notas.setWordWrap(True)
        el.addWidget(self.notas)
        self.tabs.addTab(e, "Equipos y viajes")
        self.t_norma = DataTable(["Estado", "Regla", "Detalle", "Fuente", "Verificada"], estirar=2)
        self.tabs.addTab(self.t_norma, "Normativa")
        p = QWidget(); pl = QVBoxLayout(p); pl.setContentsMargins(0, 0, 0, 0)
        aviso = QLabel("Cada parámetro indica su fuente y si fue contrastado con el texto de la norma. Los marcados «No» son "
                       "criterios de diseño o citas secundarias: confírmelos antes de usarlos como argumento legal.")
        aviso.setWordWrap(True)
        aviso.setObjectName("tenue")
        pl.addWidget(aviso)
        self.t_params = DataTable(["Clave", "Valor", "Unidad", "Descripción", "Fuente", "Verificado"], estirar=3)
        pl.addWidget(self.t_params, 1)
        ed = QFrame(); ed.setObjectName("tarjeta")
        edl = QHBoxLayout(ed)
        self.combo_param = QComboBox(); self.combo_param.setMinimumWidth(260)
        self.valor_param = QDoubleSpinBox(); self.valor_param.setRange(0.0001, 100000); self.valor_param.setDecimals(3)
        self.btn_param = QPushButton("Guardar valor"); self.btn_param.setObjectName("primario")
        self.btn_restaurar = QPushButton("Restaurar valores por defecto")
        for w in (QLabel("Parámetro:"), self.combo_param, QLabel("Valor:"), self.valor_param, self.btn_param, self.btn_restaurar):
            edl.addWidget(w)
        edl.addStretch(1)
        pl.addWidget(ed)
        self.tabs.addTab(p, "Parámetros normativos")
        self.t_alertas = DataTable(["Nivel", "Código", "Alerta", "Detalle"], estirar=3)
        self.tabs.addTab(self.t_alertas, "Alertas")
        self.cuerpo.addWidget(self.tabs, 1)
        self.cuerpo.addWidget(self.estado)

        self.btn.clicked.connect(lambda: self.analizar_solicitado.emit(int(self.combo.currentData() or 0), self.n_max.value()))
        self.btn_param.clicked.connect(lambda: self.guardar_parametro.emit(self.combo_param.currentData() or "", self.valor_param.value()))
        self.btn_restaurar.clicked.connect(self.restaurar_parametros.emit)
        self.combo_param.currentIndexChanged.connect(lambda _: self.parametro_elegido.emit(self.combo_param.currentData() or ""))

    def set_escenarios(self, opciones):
        previo = self.combo.currentData()
        self.combo.clear()
        for i, n in opciones:
            self.combo.addItem(n, i)
        self.combo.setCurrentIndex(max(self.combo.findData(previo), 0))

    def set_parametros(self, opciones):
        previo = self.combo_param.currentData()
        self.combo_param.blockSignals(True)
        self.combo_param.clear()
        for k, n in opciones:
            self.combo_param.addItem(n, k)
        self.combo_param.setCurrentIndex(max(self.combo_param.findData(previo), 0))
        self.combo_param.blockSignals(False)
