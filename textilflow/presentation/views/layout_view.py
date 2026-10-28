from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QVBoxLayout, QWidget)

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import DataTable, PageView
from ..widgets.crud_panel import CrudPanel
from ..widgets.layout_canvas import LayoutCanvasConControles
from ..widgets.adaptable import FilaAdaptable


class LayoutView(PageView):
    ruta_solicitada = pyqtSignal(str, str, float)
    limpiar_ruta_solicitado = pyqtSignal()
    pestana_cambiada = pyqtSignal()

    def __init__(self, funciones: list[tuple], origenes: list[tuple]):
        super().__init__("Layout y movimientos",
                         "Defina las áreas (Almacén → … → Despacho), los pasillos, las prendas con sus ramas de proceso y los pedidos del taller activo.",
                         theme.AZUL)
        self.tabs = QTabWidget()
        self.tabs.tabBar().setUsesScrollButtons(True)      # en ventanas angostas las pestañas se desplazan en vez de ensanchar la página
        self.tabs.tabBar().setExpanding(False)

        self.estaciones = CrudPanel(
            "Estación", "Nodos registrados",
            [CampoSpec("codigo", "Código *", placeholder="Ej.: A"),
             CampoSpec("nombre", "Nombre", placeholder="Ej.: Almacén"),
             CampoSpec("funcion", "Función en el proceso", "combo"),
             CampoSpec("x", "X (m)", "float", -10_000, 10_000, 2),
             CampoSpec("y", "Y (m)", "float", -10_000, 10_000, 2),
             CampoSpec("tiempo_proceso_min", "Tiempo (min/unidad)", "float", 0, 10_000, 3),
             CampoSpec("capacidad", "Puestos en paralelo", "int", 1, 1000, defecto=1),
             CampoSpec("grupo", "Grupo alternativo", placeholder="Ej.: COSTURA")],
            ["ID", "Código", "Nombre", "Función", "X", "Y", "min/u", "Puestos", "Grupo"], theme.AZUL, estirar=2)
        self.estaciones.set_opciones("funcion", funciones)
        n1 = QLabel("Almacén = inicio y Despacho = fin de toda ruta (solo uno de cada uno). Las áreas «Proceso» "
                    "necesitan tiempo por unidad; las que comparten grupo son alternativas (una elige la menos cargada).")
        n1.setObjectName("tenue")
        n1.setWordWrap(True)
        self.estaciones.insertar_bajo_formulario(n1)

        self.conexiones = CrudPanel(
            "Conexión", "Conexiones registradas",
            [CampoSpec("origen", "Origen", "combo"), CampoSpec("destino", "Destino", "combo"),
             CampoSpec("distancia_m", "Distancia (m)", "float", 0, 100_000, 2),
             CampoSpec("ancho_m", "Ancho pasillo (m)", "float", 0.05, 100, 2, 1.5),
             CampoSpec("bidireccional", "Bidireccional", "check", defecto=True)],
            ["ID", "Origen", "Destino", "Distancia (m)", "Ancho (m)", "Sentido"], theme.AZUL)
        nota = QLabel("Distancia = 0 → se calcula con las coordenadas de las estaciones.")
        nota.setObjectName("tenue")
        nota.setWordWrap(True)
        self.conexiones.insertar_bajo_formulario(nota)

        self.prendas = CrudPanel(
            "Tipo de prenda", "Tipos de confección",
            [CampoSpec("nombre", "Nombre *", placeholder="Ej.: Camisa"),
             CampoSpec("peso_unidad_kg", "Peso por unidad (kg)", "float", 0.001, 1000, 3, 0.3),
             CampoSpec("unidades_por_lote", "Unidades por lote", "int", 1, 100_000, defecto=24),
             CampoSpec("factor_proceso", "Factor de tiempo de proceso", "float", 0.05, 100, 2, 1.0)],
            ["ID", "Prenda", "kg/u", "Lote (u)", "Factor"], theme.AZUL, estirar=1)
        n2 = QLabel("El lote es la unidad que se procesa y se transporta junta. El factor multiplica los "
                    "tiempos de cada área (una chaqueta cose más lento que una camisa).")
        n2.setObjectName("tenue")
        n2.setWordWrap(True)
        self.prendas.insertar_bajo_formulario(n2)

        self.rutas = CrudPanel(
            "Ruta de proceso (rama)", "Ramas de cada prenda",
            [CampoSpec("tipo_prenda_id", "Prenda", "combo"),
             CampoSpec("nombre", "Nombre de la rama *", placeholder="Ej.: Con bordado"),
             CampoSpec("fraccion_pct", "% de las unidades", "float", 0.1, 100, 1, 100.0),
             CampoSpec("secuencia", "Secuencia *", "multiline", placeholder="A>C>B>@COSTURA>I>E>D")],
            ["ID", "Prenda", "Rama", "%", "Secuencia"], theme.AZUL, ancho_form=380, estirar=4)
        self.nota_rutas = QLabel("")
        self.nota_rutas.setObjectName("tenue")
        self.nota_rutas.setWordWrap(True)
        self.rutas.insertar_bajo_formulario(self.nota_rutas)

        self.pedidos = CrudPanel(
            "Pedido", "Pedidos del taller",
            [CampoSpec("tipo_prenda_id", "Prenda", "combo"),
             CampoSpec("cantidad", "Cantidad (unidades)", "int", 1, 1_000_000, defecto=100),
             CampoSpec("prioridad", "Prioridad (1 = urgente)", "int", 1, 9, defecto=3),
             CampoSpec("llegada_min", "Llega al almacén (min)", "float", 0, 100_000, 1),
             CampoSpec("vencimiento_min", "Fecha límite (min, 0 = sin)", "float", 0, 100_000, 1),
             CampoSpec("origen_datos", "Origen de datos", "combo")],
            ["ID", "Prenda", "Cantidad", "Prior.", "Llegada", "Límite", "Datos"], theme.AZUL, estirar=1)
        self.pedidos.set_opciones("origen_datos", origenes)

        self.tabs.addTab(self.estaciones, "Estaciones / Nodos")
        self.tabs.addTab(self.conexiones, "Conexiones / Arcos")
        self.tabs.addTab(self.prendas, "Prendas")
        self.tabs.addTab(self.rutas, "Rutas de proceso")
        self.tabs.addTab(self.pedidos, "Pedidos")
        self.tabs.addTab(self._crear_vista_2d(), "Vista 2D")
        self.tabs.currentChanged.connect(lambda _: self.pestana_cambiada.emit())
        self.cuerpo.addWidget(self.tabs, 1)
        self.cuerpo.addWidget(self.estado)

    def _crear_vista_2d(self) -> QWidget:
        w = QWidget()
        lay = FilaAdaptable(w)
        lay.setContentsMargins(0, 0, 0, 0)
        izq = QFrame()
        izq.setObjectName("tarjeta")
        il = QVBoxLayout(izq)
        t = QLabel("Operational Layout View / Vista operacional")
        t.setStyleSheet("font-size: 14px; font-weight: 700;")
        il.addWidget(t)
        self.mapa = LayoutCanvasConControles()
        il.addWidget(self.mapa, 1)
        lay.addWidget(izq, 3)

        der = QFrame()
        der.setObjectName("tarjeta")
        dl = QVBoxLayout(der)
        titulo = QLabel("ROUTE ANALYSIS")
        titulo.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {theme.AZUL}; padding-left: 8px;")
        dl.addWidget(titulo)
        g = QGridLayout()
        self.ruta_origen, self.ruta_destino = QComboBox(), QComboBox()
        self.ruta_ancho = QDoubleSpinBox()
        self.ruta_ancho.setRange(0, 100)
        self.ruta_ancho.setDecimals(2)
        self.ruta_ancho.setSuffix(" m")
        g.addWidget(QLabel("Origen"), 0, 0)
        g.addWidget(self.ruta_origen, 0, 1)
        g.addWidget(QLabel("Destino"), 1, 0)
        g.addWidget(self.ruta_destino, 1, 1)
        g.addWidget(QLabel("Ancho mín."), 2, 0)
        g.addWidget(self.ruta_ancho, 2, 1)
        dl.addLayout(g)
        botones = QHBoxLayout()
        calc = QPushButton("Calcular ruta")
        calc.setObjectName("primario")
        limpiar = QPushButton("Limpiar")
        botones.addWidget(calc)
        botones.addWidget(limpiar)
        dl.addLayout(botones)
        self.ruta_resumen = QLabel("Sin ruta activa.")
        self.ruta_resumen.setWordWrap(True)
        dl.addWidget(self.ruta_resumen)
        self.ruta_tramos = DataTable(["#", "Tramo", "Dist. (m)", "Ancho (m)"], estirar=1)
        dl.addWidget(self.ruta_tramos, 1)
        lay.addWidget(der, 2)
        calc.clicked.connect(lambda: self.ruta_solicitada.emit(
            self.ruta_origen.currentData() or "", self.ruta_destino.currentData() or "", self.ruta_ancho.value()))
        limpiar.clicked.connect(self.limpiar_ruta_solicitado.emit)
        return w

    def set_codigos(self, opciones: list[tuple]) -> None:
        for c in ("origen", "destino"):
            self.conexiones.set_opciones(c, opciones)
        for combo in (self.ruta_origen, self.ruta_destino):
            actual = combo.currentData()
            combo.clear()
            for v, e in opciones:
                combo.addItem(e, v)
            i = combo.findData(actual)
            combo.setCurrentIndex(max(i, 0))
        if self.ruta_destino.count() > 1 and self.ruta_destino.currentIndex() == self.ruta_origen.currentIndex():
            self.ruta_destino.setCurrentIndex(1)

    def mostrar_ruta(self, resumen: str, filas: list) -> None:
        self.ruta_resumen.setText(resumen)
        self.ruta_tramos.set_filas(filas)

    def dibujar_red(self, nodos, arcos) -> None:
        self.mapa.dibujar(nodos, arcos)

    def set_prendas(self, opciones: list[tuple]) -> None:
        self.rutas.set_opciones("tipo_prenda_id", opciones)
        self.pedidos.set_opciones("tipo_prenda_id", opciones)

    def set_ayuda_rutas(self, texto: str) -> None:
        self.nota_rutas.setText(texto)
