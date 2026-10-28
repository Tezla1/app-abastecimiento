# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Página de Layout y movimientos, con una pestaña por tipo de dato y la vista 2D con cálculo de rutas.

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QVBoxLayout, QWidget)

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import TablaDatos, VistaPagina
from ..widgets.panel_crud import PanelCrud
from ..widgets.lienzo_layout import LienzoLayoutConControles
from ..widgets.adaptable import FilaAdaptable


class LayoutView(VistaPagina):
    ruta_solicitada = pyqtSignal(str, str, float)
    limpiar_ruta_solicitado = pyqtSignal()
    pestana_cambiada = pyqtSignal()
    aviso_solicitado = pyqtSignal(int)
    copiar_aviso_solicitado = pyqtSignal()

    def __init__(self, funciones: list[tuple], origenes: list[tuple], estados_compra: list[tuple]):
        super().__init__("Layout y movimientos",
                         "Defina las áreas (Almacén → … → Despacho), los pasillos, las prendas con sus ramas de proceso y los pedidos y el inventario del taller activo.",
                         theme.AZUL)
        self.tabs = QTabWidget()
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)

        self.estaciones = PanelCrud(
            "Estación", "Nodos registrados",
            [CampoSpec("codigo", "Código *", placeholder="Ej.: A", ayuda="Código corto y único del área o nodo (letras/números). Ej.: A = Almacén, C = Corte, D = Despacho. Se usa en las rutas de proceso."),
             CampoSpec("nombre", "Nombre", placeholder="Ej.: Almacén", ayuda="Nombre del área o estación. Ej.: Almacén, Corte, Despacho."),
             CampoSpec("funcion", "Función en el proceso", "combo", ayuda="Papel del área: Almacén (punto inicial), Despacho (punto final), Área de proceso, Punto de espera/buffer o Base del recurso. Debe haber un Almacén y un Despacho."),
             CampoSpec("x", "X (m)", "float", -10_000, 10_000, 2, ayuda="Posición horizontal del área en el plano, en metros (m), medida desde el origen (0, 0) del taller."),
             CampoSpec("y", "Y (m)", "float", -10_000, 10_000, 2, ayuda="Posición vertical del área en el plano, en metros (m), medida desde el origen (0, 0) del taller."),
             CampoSpec("tiempo_proceso_min", "Tiempo (min/unidad)", "float", 0, 10_000, 3, ayuda="Minutos que tarda procesar UNA unidad en este puesto (min/unidad). Ej.: 0,5 = 30 segundos. Use 0 si es solo paso o almacenamiento."),
             CampoSpec("capacidad", "Puestos en paralelo", "int", 1, 1000, defecto=1, ayuda="Cantidad de puestos o máquinas que trabajan en paralelo en esta área (entero ≥ 1)."),
             CampoSpec("grupo", "Grupo alternativo", placeholder="Ej.: COSTURA", ayuda="Nombre de un grupo de áreas equivalentes (Ej.: COSTURA). En las rutas se escribe «@COSTURA» para elegir la menos cargada. Opcional.")],
            ["ID", "Código", "Nombre", "Función", "X", "Y", "min/u", "Puestos", "Grupo"], theme.AZUL, estirar=2)
        self.estaciones.set_opciones("funcion", funciones)
        n1 = QLabel("Almacén = inicio y Despacho = fin de toda ruta (solo uno de cada uno). Las áreas «Proceso» "
                    "necesitan tiempo por unidad; las que comparten grupo son alternativas (una elige la menos cargada).")
        n1.setObjectName("tenue")
        n1.setWordWrap(True)
        self.estaciones.insertar_bajo_formulario(n1)

        self.conexiones = PanelCrud(
            "Conexión", "Conexiones registradas",
            [CampoSpec("origen", "Origen", "combo", ayuda="Área de donde sale el material por este pasillo."), CampoSpec("destino", "Destino", "combo", ayuda="Área a la que llega el material por este pasillo."),
             CampoSpec("distancia_m", "Distancia (m)", "float", 0, 100_000, 2, ayuda="Longitud real del recorrido entre origen y destino, en metros (m), medida por el pasillo (no en línea recta)."),
             CampoSpec("ancho_m", "Ancho pasillo (m)", "float", 0.05, 100, 2, 1.5, ayuda="Ancho libre del pasillo en metros (m). Debe ser mayor que el ancho del robot para que pueda pasar."),
             CampoSpec("bidireccional", "Bidireccional", "check", defecto=True, ayuda="Marcado: se puede circular en ambos sentidos. Desmarcado: solo de origen a destino.")],
            ["ID", "Origen", "Destino", "Distancia (m)", "Ancho (m)", "Sentido"], theme.AZUL)
        nota = QLabel("Distancia = 0 → se calcula con las coordenadas de las estaciones.")
        nota.setObjectName("tenue")
        nota.setWordWrap(True)
        self.conexiones.insertar_bajo_formulario(nota)

        self.prendas = PanelCrud(
            "Tipo de prenda", "Tipos de confección",
            [CampoSpec("nombre", "Nombre *", placeholder="Ej.: Camisa", ayuda="Nombre del tipo de prenda. Ej.: Camisa, Pantalón. Obligatorio."),
             CampoSpec("peso_unidad_kg", "Peso por unidad (kg)", "float", 0.001, 1000, 3, 0.3, ayuda="Peso de una prenda terminada en kilogramos (kg). Ej.: camisa ≈ 0,3 kg. Sirve para calcular la carga transportada."),
             CampoSpec("unidades_por_lote", "Unidades por lote", "int", 1, 100_000, defecto=24, ayuda="Cuántas prendas van juntas en cada lote de transporte (entero ≥ 1). Ej.: 24."),
             CampoSpec("factor_proceso", "Factor de tiempo de proceso", "float", 0.05, 100, 2, 1.0, ayuda="Multiplicador de los tiempos de proceso para esta prenda. 1,0 = tiempo base; 1,5 = 50 % más lento; 0,8 = 20 % más rápido.")],
            ["ID", "Prenda", "kg/u", "Lote (u)", "Factor"], theme.AZUL, estirar=1)
        n2 = QLabel("El lote es la unidad que se procesa y se transporta junta. El factor multiplica los "
                    "tiempos de cada área (una chaqueta cose más lento que una camisa).")
        n2.setObjectName("tenue")
        n2.setWordWrap(True)
        self.prendas.insertar_bajo_formulario(n2)

        self.rutas = PanelCrud(
            "Ruta de proceso (rama)", "Ramas de cada prenda",
            [CampoSpec("tipo_prenda_id", "Prenda", "combo", ayuda="Prenda a la que pertenece este registro."),
             CampoSpec("nombre", "Nombre de la rama *", placeholder="Ej.: Con bordado", ayuda="Nombre de esta ruta o rama de la prenda. Ej.: Línea normal, Con bordado. Obligatorio."),
             CampoSpec("fraccion_pct", "% de las unidades", "float", 0.1, 100, 1, 100.0, ayuda="Porcentaje de las unidades de esta prenda que sigue esta rama (0,1 a 100). Las ramas de una misma prenda deben sumar 100 %."),
             CampoSpec("secuencia", "Secuencia *", "multiline", placeholder="A>C>B>@COSTURA>I>E>D", ayuda="Pasos separados por «>», con códigos de área. Ej.: A>C>@COSTURA>I>E>D. Debe empezar en el Almacén (A) y terminar en el Despacho (D). «@GRUPO» elige la menos cargada del grupo.")],
            ["ID", "Prenda", "Rama", "%", "Secuencia"], theme.AZUL, ancho_form=380, estirar=4)
        self.nota_rutas = QLabel("")
        self.nota_rutas.setObjectName("tenue")
        self.nota_rutas.setWordWrap(True)
        self.rutas.insertar_bajo_formulario(self.nota_rutas)

        self.pedidos = PanelCrud(
            "Pedido", "Pedidos del taller",
            [CampoSpec("tipo_prenda_id", "Prenda", "combo", ayuda="Prenda a la que pertenece este registro."),
             CampoSpec("cantidad", "Cantidad (unidades)", "int", 1, 1_000_000, defecto=100, ayuda="Número de prendas del pedido (entero ≥ 1)."),
             CampoSpec("prioridad", "Prioridad (1 = urgente)", "int", 1, 9, defecto=3, ayuda="De 1 a 9: 1 es la más urgente y 9 la menos urgente."),
             CampoSpec("llegada_min", "Llega al almacén (min)", "float", 0, 100_000, 1, ayuda="Minuto de la simulación en que el pedido llega al almacén. 0 = al iniciar el turno."),
             CampoSpec("vencimiento_min", "Fecha límite (min, 0 = sin)", "float", 0, 100_000, 1, ayuda="Minuto límite para entregar el pedido. Use 0 si no tiene fecha límite."),
             CampoSpec("origen_datos", "Origen de datos", "combo", ayuda="«Real» si el pedido es de producción real, «Sintético» si es de ejemplo o supuesto, «Diseño / conceptual» si es parte de una propuesta.")],
            ["ID", "Prenda", "Cantidad", "Prior.", "Llegada", "Límite", "Datos"], theme.AZUL, estirar=1)
        self.pedidos.set_opciones("origen_datos", origenes)

        self.inventario = PanelCrud(
            "Unidades en el almacén", "Inventario del taller",
            [CampoSpec("tipo_prenda_id", "Prenda", "combo", ayuda="Prenda de la que se registran las unidades disponibles."),
             CampoSpec("unidades", "Unidades en almacén", "int", 0, 10_000_000, defecto=0,
                       ayuda="Cuántas unidades de esta prenda hay hoy disponibles en el almacén del taller (entero ≥ 0). Si llega a 0 se genera una alerta crítica."),
             CampoSpec("stock_minimo", "Stock mínimo (aviso)", "int", 0, 10_000_000, defecto=0,
                       ayuda="Cantidad a partir de la cual se avisa que hay que reponer. Al comprar se pide lo necesario para cubrir los pedidos y dejar este mínimo.")],
            ["ID", "Prenda", "En almacén", "Mínimo", "Pedidos", "En compra", "Faltan", "Estado"], theme.NARANJA, estirar=1)
        self.nota_inventario = QLabel("Registre cuántas unidades hay en el almacén. Si no alcanzan para los pedidos o se "
                                      "agotan, aparece una alerta y puede generar el aviso de compra para Compras.")
        self.nota_inventario.setObjectName("tenue")
        self.nota_inventario.setWordWrap(True)
        self.btn_aviso = QPushButton("Generar aviso de compra")
        self.btn_aviso.setToolTip("Crea una solicitud de compra pendiente con la cantidad que falta para cubrir los pedidos y el stock mínimo.")
        self.inventario.insertar_bajo_formulario(self.btn_aviso)
        self.inventario.insertar_bajo_formulario(self.nota_inventario)
        self.btn_aviso.clicked.connect(lambda: self.aviso_solicitado.emit(int(self.inventario.widget("tipo_prenda_id").currentData() or 0)))

        self.compras = PanelCrud(
            "Aviso de compra", "Solicitudes de compra",
            [CampoSpec("tipo_prenda_id", "Prenda", "combo", ayuda="Prenda que se debe comprar."),
             CampoSpec("cantidad", "Cantidad (unidades)", "int", 1, 10_000_000, defecto=100, ayuda="Unidades que Compras debe pedir (entero ≥ 1)."),
             CampoSpec("estado", "Estado", "combo", ayuda="Pendiente: Compras aún no pide. Pedida: ya se hizo el pedido. Recibida: llegó y se suma al stock (no se puede revertir). Cancelada: no se comprará."),
             CampoSpec("nota", "Nota", "multiline", ayuda="Proveedor, fecha estimada de llegada, número de orden u otra observación. Opcional.")],
            ["ID", "Fecha", "Prenda", "Cantidad", "Estado", "Nota"], theme.NARANJA, estirar=5)
        self.compras.set_opciones("estado", estados_compra)
        self.btn_copiar = QPushButton("Copiar aviso para Compras")
        self.btn_copiar.setToolTip("Copia al portapapeles un mensaje con todo lo que está pendiente de pedir, listo para enviar a Compras.")
        self.compras.insertar_bajo_formulario(self.btn_copiar)
        self.btn_copiar.clicked.connect(self.copiar_aviso_solicitado.emit)

        self.tabs.addTab(self.estaciones, "Estaciones / Nodos")
        self.tabs.addTab(self.conexiones, "Conexiones / Arcos")
        self.tabs.addTab(self.prendas, "Prendas")
        self.tabs.addTab(self.rutas, "Rutas de proceso")
        self.tabs.addTab(self.pedidos, "Pedidos")
        self.tabs.addTab(self.inventario, "Inventario")
        self.tabs.addTab(self.compras, "Compras")
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
        t = QLabel("Vista operacional del layout")
        t.setStyleSheet("font-size: 14px; font-weight: 700;")
        il.addWidget(t)
        self.mapa = LienzoLayoutConControles()
        il.addWidget(self.mapa, 1)
        lay.addWidget(izq, 3)

        der = QFrame()
        der.setObjectName("tarjeta")
        dl = QVBoxLayout(der)
        titulo = QLabel("ANÁLISIS DE RUTA")
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
        self.ruta_tramos = TablaDatos(["#", "Tramo", "Dist. (m)", "Ancho (m)"], estirar=1)
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
        self.inventario.set_opciones("tipo_prenda_id", opciones)
        self.compras.set_opciones("tipo_prenda_id", opciones)

    def set_ayuda_rutas(self, texto: str) -> None:
        self.nota_rutas.setText(texto)
