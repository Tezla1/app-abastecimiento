from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout)

from .. import theme
from ..widgets.common import DataTable, PageView
from ..widgets.line_chart import LineChart
from ..widgets.mapa_operativo import MODOS_CALOR, MapaOperativo

VELOCIDADES = [("×0.1", 0.1), ("×0.25", 0.25), ("×0.5", 0.5), ("×1", 1), ("×2", 2), ("×5", 5), ("×20", 20),
               ("×60", 60), ("×150", 150), ("×400", 400)]


class MapaView(PageView):
    simular_solicitado = pyqtSignal(int)
    pedido_cambiado = pyqtSignal()
    modo_cambiado = pyqtSignal(str)
    jugar_solicitado = pyqtSignal()
    reiniciar_solicitado = pyqtSignal()
    velocidad_cambiada = pyqtSignal(float)
    tiempo_solicitado = pyqtSignal(float)

    def __init__(self):
        super().__init__("Mapa operativo",
                         "Simulación animada del turno (use ×0.1 a ×1 para ver cada recorrido): los recursos recorren la red, las áreas muestran cola y ocupación y el "
                         "mapa de calor se acumula con el tiempo. Pulse un área para ver las rutas que usarán los lotes.",
                         theme.VERDE)
        barra = QFrame(); barra.setObjectName("tarjeta")
        bl = QHBoxLayout(barra)
        bl.addWidget(QLabel("Escenario:"))
        self.combo_esc = QComboBox(); self.combo_esc.setMinimumWidth(230)
        bl.addWidget(self.combo_esc)
        bl.addWidget(QLabel("Pedido:"))
        self.combo_pedido = QComboBox(); self.combo_pedido.setMinimumWidth(200)
        bl.addWidget(self.combo_pedido)
        bl.addWidget(QLabel("Mapa de calor:"))
        self.combo_modo = QComboBox()
        for k, n in MODOS_CALOR:
            self.combo_modo.addItem(n, k)
        bl.addWidget(self.combo_modo)
        self.btn_simular = QPushButton("Simular y animar")
        self.btn_simular.setObjectName("primario")
        bl.addWidget(self.btn_simular)
        self.cuerpo.addWidget(barra)

        medio = QHBoxLayout()
        izq = QVBoxLayout()
        caja = QFrame(); caja.setObjectName("tarjeta")
        cl = QVBoxLayout(caja)
        self.mapa = MapaOperativo()
        cl.addWidget(self.mapa, 1)
        ctrl = QHBoxLayout()
        self.btn_jugar = QPushButton("▶ Reproducir")
        self.btn_jugar.setObjectName("primario")
        self.btn_reiniciar = QPushButton("⏮")
        self.btn_reiniciar.setFixedWidth(40)
        self.combo_vel = QComboBox()
        for n, v in VELOCIDADES:
            self.combo_vel.addItem(f"{n} min sim./s", v)
        self.combo_vel.setCurrentIndex(3)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.reloj = QLabel("t = 0 min")
        self.reloj.setMinimumWidth(190)
        self.reloj.setStyleSheet("font-weight: 700;")
        for w in (self.btn_jugar, self.btn_reiniciar, self.combo_vel):
            ctrl.addWidget(w)
        ctrl.addWidget(self.slider, 1)
        ctrl.addWidget(self.reloj)
        cl.addLayout(ctrl)
        leyenda = QHBoxLayout()
        grad = QLabel("")
        grad.setFixedSize(180, 10)
        grad.setStyleSheet(f"background: {theme.GRADIENTE_CSS}; border-radius: 4px;")
        leyenda.addWidget(QLabel("poco"))
        leyenda.addWidget(grad)
        leyenda.addWidget(QLabel("mucho tránsito"))
        leyenda.addSpacing(18)
        self.leyenda_recursos = QLabel("")
        leyenda.addWidget(self.leyenda_recursos, 1)
        cl.addLayout(leyenda)
        izq.addWidget(caja, 3)
        caja2 = QFrame(); caja2.setObjectName("tarjeta")
        c2 = QVBoxLayout(caja2)
        self.grafico = LineChart("Lotes en el sistema, completados y esperando (cursor = instante actual)", "min")
        self.grafico.setMinimumHeight(140)
        c2.addWidget(self.grafico)
        izq.addWidget(caja2, 1)
        medio.addLayout(izq, 3)

        der = QFrame(); der.setObjectName("tarjeta"); der.setMinimumWidth(470)
        dl = QVBoxLayout(der)
        t = QLabel("Rutas del nodo seleccionado")
        t.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {theme.VERDE}; padding-left: 8px;")
        dl.addWidget(t)
        self.info_nodo = QLabel("Pulse un área del mapa. Se resaltan las rutas que realmente usarán los lotes que pasan "
                                "por ella (la principal en amarillo, las alternativas en naranja).")
        self.info_nodo.setWordWrap(True)
        self.info_nodo.setObjectName("tenue")
        dl.addWidget(self.info_nodo)
        self.tabla_rutas = DataTable(["Ped.", "Prenda · rama", "Camino", "m", "Lotes", "Unid."], estirar=2)
        dl.addWidget(self.tabla_rutas, 2)
        t2 = QLabel("Estado en este instante")
        t2.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {theme.AZUL}; padding-left: 8px;")
        dl.addWidget(t2)
        self.tabla_areas = DataTable(["Área", "En cola", "En proceso", "Util. turno %"], estirar=0)
        dl.addWidget(self.tabla_areas, 2)
        self.estado_global = QLabel("")
        self.estado_global.setWordWrap(True)
        dl.addWidget(self.estado_global)
        medio.addWidget(der, 1)
        self.cuerpo.addLayout(medio, 1)
        self.cuerpo.addWidget(self.estado)

        self.btn_simular.clicked.connect(lambda: self.simular_solicitado.emit(int(self.combo_esc.currentData() or 0)))
        self.combo_pedido.currentIndexChanged.connect(lambda _: self.pedido_cambiado.emit())
        self.combo_modo.currentIndexChanged.connect(lambda _: self.modo_cambiado.emit(self.combo_modo.currentData()))
        self.btn_jugar.clicked.connect(self.jugar_solicitado.emit)
        self.btn_reiniciar.clicked.connect(self.reiniciar_solicitado.emit)
        self.combo_vel.currentIndexChanged.connect(lambda _: self.velocidad_cambiada.emit(float(self.combo_vel.currentData())))
        self.slider.sliderMoved.connect(lambda v: self.tiempo_solicitado.emit(v / 1000.0))

    def set_escenarios(self, opciones):
        previo = self.combo_esc.currentData()
        self.combo_esc.clear()
        for i, n in opciones:
            self.combo_esc.addItem(n, i)
        self.combo_esc.setCurrentIndex(max(self.combo_esc.findData(previo), 0))

    def set_pedidos(self, opciones):
        previo = self.combo_pedido.currentData()
        self.combo_pedido.blockSignals(True)
        self.combo_pedido.clear()
        self.combo_pedido.addItem("Todos los pedidos", None)
        for i, n in opciones:
            self.combo_pedido.addItem(n, i)
        self.combo_pedido.setCurrentIndex(max(self.combo_pedido.findData(previo), 0))
        self.combo_pedido.blockSignals(False)

    def set_jugando(self, jugando: bool) -> None:
        self.btn_jugar.setText("⏸ Pausa" if jugando else "▶ Reproducir")
