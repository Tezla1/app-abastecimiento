from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout

from .. import theme
from ..widgets.common import KpiCard, PageView
from ..widgets.common import DataTable
from ..widgets.mapa_operativo import MapaOperativo
from ..widgets.adaptable import FilaAdaptable, FlujoLayout


class DashboardView(PageView):
    def __init__(self):
        super().__init__("Dashboard de operaciones e investigación",
                         "Intralogística · Optimización · Simulación · Investigación aplicada", theme.AZUL)
        fila = FlujoLayout()
        self.k_talleres = KpiCard("Talleres", "#1F4E9E", self)
        self.k_estaciones = KpiCard("Áreas", "#1B7A57", self)
        self.k_conexiones = KpiCard("Conexiones", "#B8701A", self)
        self.k_pedidos = KpiCard("Pedidos", "#6B43A8", self)
        self.k_escenarios = KpiCard("Escenarios", "#187A7E", self)
        self.k_alertas = KpiCard("Alertas", "#8C3A44", self)
        for k in (self.k_talleres, self.k_estaciones, self.k_conexiones, self.k_pedidos, self.k_escenarios, self.k_alertas):
            fila.addWidget(k)
        self.cuerpo.addLayout(fila)

        medio = FilaAdaptable()
        caja = QFrame()
        caja.setObjectName("tarjeta")
        cl = QVBoxLayout(caja)
        t = QLabel("Mapa de calor del taller")
        t.setStyleSheet("font-size: 14px; font-weight: 700;")
        s = QLabel("Pasadas acumuladas del último escenario simulado · grosor y color = tránsito")
        s.setObjectName("subtitulo")
        cl.addWidget(t)
        cl.addWidget(s)
        self.mapa = MapaOperativo()
        self.mapa.setMinimumHeight(300)
        cl.addWidget(self.mapa, 1)
        cl.addWidget(self._leyenda())
        medio.addWidget(caja, 3)

        derecha = QVBoxLayout()
        ind = QFrame()
        ind.setObjectName("tarjeta")
        il = QGridLayout(ind)
        titulo = QLabel("Indicadores clave")
        titulo.setStyleSheet("font-size: 14px; font-weight: 700;")
        il.addWidget(titulo, 0, 0, 1, 2)
        self._ind = {}
        for i, (clave, nombre) in enumerate([("dist", "Distancia red"), ("ancho", "Ancho mín. pasillo"),
                                              ("carga", "Prendas definidas"), ("sim", "Escenarios simulados")]):
            caja_i = QFrame()
            caja_i.setStyleSheet(f"background: {theme.PANEL_2}; border-radius: 8px;")
            li = QVBoxLayout(caja_i)
            n = QLabel(nombre)
            n.setObjectName("tenue")
            v = QLabel("—")
            v.setStyleSheet("font-size: 16px; font-weight: 700;")
            li.addWidget(n)
            li.addWidget(v)
            il.addWidget(caja_i, 1 + i // 2, i % 2)
            self._ind[clave] = v
        derecha.addWidget(ind)

        al_box = QFrame()
        al_box.setObjectName("tarjeta")
        alb = QVBoxLayout(al_box)
        ta2 = QLabel("Alertas principales")
        ta2.setStyleSheet("font-size: 14px; font-weight: 700;")
        alb.addWidget(ta2)
        self.tabla_alertas = DataTable(["Nivel", "Alerta"], estirar=1)
        alb.addWidget(self.tabla_alertas)
        derecha.addWidget(al_box, 1)

        act = QFrame()
        act.setObjectName("tarjeta")
        al = QVBoxLayout(act)
        ta = QLabel("Actividad reciente")
        ta.setStyleSheet("font-size: 14px; font-weight: 700;")
        al.addWidget(ta)
        self._actividad = QLabel("")
        self._actividad.setWordWrap(True)
        self._actividad.setStyleSheet("line-height: 160%;")
        al.addWidget(self._actividad)
        al.addStretch(1)
        derecha.addWidget(act)
        medio.addLayout(derecha, 1)
        self.cuerpo.addLayout(medio, 1)

    def _leyenda(self) -> QFrame:
        marco = QFrame()
        marco.setStyleSheet(f"background: {theme.PANEL_2}; border-radius: 8px;")
        lay = QHBoxLayout(marco)
        lay.setContentsMargins(12, 6, 12, 6)
        titulo = QLabel("Cómo leer los colores")
        titulo.setStyleSheet("font-weight: 700;")
        lay.addWidget(titulo)
        lay.addWidget(QLabel("Poco tránsito"))
        barra = QFrame()
        barra.setFixedSize(150, 10)
        barra.setStyleSheet(f"background: {theme.GRADIENTE_CSS}; border-radius: 5px;")
        lay.addWidget(barra)
        lay.addWidget(QLabel("Mucho tránsito"))
        nota = QLabel("Azul y verde: pasillo despejado · amarillo: movimiento normal · rojo: el más cargado, conviene vigilarlo. "
                      "Línea más gruesa = más viajes. Gris tenue: casi sin uso.")
        nota.setObjectName("tenue")
        nota.setWordWrap(True)
        lay.addWidget(nota, 1)
        return marco

    def mostrar_kpis(self, talleres: int, estaciones: int, conexiones: int, pedidos: int, escenarios: int, alertas: int) -> None:
        self.k_talleres.set_valor(str(talleres), "Registrados")
        self.k_estaciones.set_valor(str(estaciones), "Áreas del taller activo")
        self.k_conexiones.set_valor(str(conexiones), "Conexiones registradas")
        self.k_pedidos.set_valor(str(pedidos), "Pedidos del taller")
        self.k_escenarios.set_valor(str(escenarios), "Escenarios definidos")
        self.k_alertas.set_valor(str(alertas), "Configuración, norma y simulación")

    def mostrar_indicadores(self, distancia: str, ancho: str, prendas: str, simulados: str) -> None:
        self._ind["dist"].setText(distancia)
        self._ind["ancho"].setText(ancho)
        self._ind["carga"].setText(prendas)
        self._ind["sim"].setText(simulados)

    def mostrar_actividad(self, lineas: list[str]) -> None:
        self._actividad.setText("\n".join(f"●  {l}" for l in lineas))

    def dibujar_red(self, nodos, arcos, trafico=None) -> None:
        self.mapa.dibujar(nodos, arcos)
        self.mapa.cargar_animacion(None)
        self.mapa.calor_estatico(trafico or {})
