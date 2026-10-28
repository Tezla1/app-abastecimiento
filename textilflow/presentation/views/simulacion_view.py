from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox, QTabWidget,
                             QVBoxLayout, QWidget)

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import TablaDatos, TarjetaKpi, VistaPagina
from ..widgets.panel_crud import PanelCrud
from ..widgets.estabilidad import Estabilidad
from ..widgets.grafico_lineas import GraficoLineas
from ..widgets.adaptable import FilaAdaptable, FlujoLayout


class SimulacionView(VistaPagina):
    ejecutar_solicitado = pyqtSignal(int)
    replicas_solicitadas = pyqtSignal(int, int)

    def __init__(self, tipos: list[tuple], politicas: list[tuple]):
        super().__init__("Escenarios y simulación",
                         "Condiciones base y simulación de eventos discretos del proceso completo: cada lote recorre su ruta "
                         "(Almacén → áreas en paralelo → Despacho), con colas, prioridades y transporte por recursos.",
                         theme.VERDE)
        self.tabs = QTabWidget()
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        campos = [
            CampoSpec("nombre", "Nombre *", placeholder="Ej.: S1 · AMR (2 robots)", ayuda="Nombre del escenario. Ej.: «S1 · AMR (2 robots)». Obligatorio."),
            CampoSpec("tipo", "Tipo", "combo", ayuda="S0 · Manual: el material lo mueven operarios (línea base). S1 · AMR: lo mueven robots autónomos."),
            CampoSpec("robot_id", "Perfil de robot", "combo", ayuda="Perfil de robot (de la pantalla «Diseño conceptual del robot») que se usa en este escenario. Solo aplica a escenarios con robots."),
            CampoSpec("num_recursos", "N.º de recursos", "int", 1, 1000, defecto=1, ayuda="Cantidad de transportadores (robots u operarios) que mueven el material al mismo tiempo (entero ≥ 1)."),
            CampoSpec("tiempo_observacion_min", "Turno / observación (min)", "float", 1, 100_000, 0, 480.0, ayuda="Duración del turno simulado en minutos. Ej.: 480 min = 8 horas."),
            CampoSpec("velocidad_ms", "Velocidad (m/s)", "float", 0.01, 100, 3, 1.0, ayuda="Velocidad de traslado del transportador en metros por segundo (m/s). Ej.: 1,0 m/s = 3,6 km/h."),
            CampoSpec("capacidad_kg", "Capacidad por viaje (kg)", "float", 0.1, 100_000, 1, 25.0, ayuda="Peso máximo que se transporta por viaje, en kilogramos (kg)."),
            CampoSpec("t_carga_s", "Carga (s)", "float", 0, 10_000, 1, 30.0, ayuda="Segundos que tarda en cargar el material en cada viaje (s)."),
            CampoSpec("t_descarga_s", "Descarga (s)", "float", 0, 10_000, 1, 30.0, ayuda="Segundos que tarda en descargar el material en cada viaje (s)."),
            CampoSpec("nodo_inicial", "Nodo inicial del recurso", "combo", ayuda="Área donde empieza cada transportador al iniciar la simulación."),
            CampoSpec("reposicionamiento", "Reposicionamiento vacío", "check", defecto=True, ayuda="Marcado: el transportador vacío va solo hacia donde hay trabajo pendiente. Desmarcado: espera donde terminó."),
            CampoSpec("politica", "Política de despacho", "combo", ayuda="Prioridad: atiende primero el pedido más urgente (1 = más urgente). FIFO: atiende por orden de llegada."),
            CampoSpec("balanceo", "Balancear grupos de áreas", "check", defecto=True, ayuda="Marcado: reparte el trabajo entre las áreas de un mismo grupo (Ej.: COSTURA) según la carga de cada una."),
            CampoSpec("factor_demanda_pct", "Demanda (% de los pedidos)", "float", 1, 1000, 0, 100.0, ayuda="Porcentaje de los pedidos que se simula. 100 % = demanda normal; 150 % = 50 % más pedidos (prueba de estrés)."),
            CampoSpec("variabilidad_pct", "Variabilidad de tiempos ± %", "float", 0, 99, 0, 0.0, ayuda="Variación aleatoria ± % aplicada a los tiempos de proceso. 0 % = tiempos exactos; 10 % = cada tiempo varía hasta ±10 %."),
            CampoSpec("semilla", "Semilla aleatoria", "int", 0, 999_999, defecto=1, ayuda="Número que fija la aleatoriedad: la misma semilla da siempre el mismo resultado, lo que permite repetir y comparar."),
        ]
        self.panel = PanelCrud("Escenario · condiciones base", "Escenarios del taller activo", campos,
                               ["ID", "Nombre", "Tipo", "Recursos", "Política", "Demanda %", "Registros"],
                               theme.VERDE, ancho_form=390, estirar=1)
        self.panel.set_opciones("tipo", tipos)
        self.panel.set_opciones("politica", politicas)
        self.btn_simular = QPushButton("Guardar y simular el turno")
        self.btn_simular.setObjectName("primario")
        self.panel.insertar_bajo_formulario(self.btn_simular)
        self.tabs.addTab(self.panel, "Escenarios · condiciones base")

        res = QWidget()
        rl = QVBoxLayout(res)
        rl.setContentsMargins(0, 0, 0, 0)
        self.resumen = QLabel("Ejecute una simulación para ver sus resultados.")
        self.resumen.setWordWrap(True)
        rl.addWidget(self.resumen)
        fila = FlujoLayout()
        colores = ["#1B7A57", "#1F4E9E", "#6B43A8", "#B8701A", "#8C3A44", "#187A7E"]
        nombres = ["Lotes completados", "Cierre última entrega", "Lead time medio", "Pedidos a tiempo",
                   "Espera por transporte", "Utilización flota"]
        self.kpis = [TarjetaKpi(n, c) for n, c in zip(nombres, colores)]
        for k in self.kpis:
            fila.addWidget(k)
        rl.addLayout(fila)
        graficos = FilaAdaptable()
        self.g_wip = GraficoLineas("Lotes en el sistema y completados", "min")
        self.g_cola = GraficoLineas("Lotes esperando en cada área", "min")
        for g in (self.g_wip, self.g_cola):
            caja = QFrame(); caja.setObjectName("tarjeta")
            cl = QVBoxLayout(caja); cl.addWidget(g)
            graficos.addWidget(caja)
        rl.addLayout(graficos, 2)
        abajo = FilaAdaptable()
        caja_a = QFrame(); caja_a.setObjectName("tarjeta")
        la = QVBoxLayout(caja_a)
        sub = QLabel("Estado de las áreas")
        sub.setStyleSheet("font-size: 13px; font-weight: 700;")
        nota = QLabel("Utilización simulada frente a la carga que le llega al área (ρ). Rojo: al límite.")
        nota.setObjectName("tenue")
        la.addWidget(sub)
        la.addWidget(nota)
        self.tabla = TablaDatos(["Área", "Puestos", "Util. %", "Carga ρ %", "Espera min", "Espera máx.", "Cola máx.",
                                "Lotes", "Unid."], estirar=None)
        la.addWidget(self.tabla, 1)
        abajo.addWidget(caja_a, 5)
        caja_b = QFrame(); caja_b.setObjectName("tarjeta")
        lb = QVBoxLayout(caja_b)
        sub2 = QLabel("Alertas del escenario")
        sub2.setStyleSheet("font-size: 13px; font-weight: 700;")
        nota2 = QLabel("Lo que conviene revisar primero, de más a menos grave.")
        nota2.setObjectName("tenue")
        lb.addWidget(sub2)
        lb.addWidget(nota2)
        self.tabla_alertas = TablaDatos(["Nivel", "Código", "Alerta", "Detalle", "Posible solución"], estirar=3)
        self.tabla_alertas.texto_largo((2, 3, 4), (3, 3, 5))
        lb.addWidget(self.tabla_alertas, 1)
        abajo.addWidget(caja_b, 4)
        rl.addLayout(abajo, 3)
        self.tabs.addTab(res, "Resultados")

        rep = QWidget()
        pl = QVBoxLayout(rep)
        pl.setContentsMargins(0, 0, 0, 0)
        barra = QFrame(); barra.setObjectName("tarjeta")
        bl = FilaAdaptable(barra)
        bl.addWidget(QLabel("Escenario:"))
        self.combo_rep = QComboBox()
        bl.addWidget(self.combo_rep, 1)
        bl.addWidget(QLabel("N.º de réplicas:"))
        self.n_rep = QSpinBox(); self.n_rep.setRange(2, 500); self.n_rep.setValue(30)
        bl.addWidget(self.n_rep)
        self.btn_rep = QPushButton("Ejecutar réplicas")
        self.btn_rep.setObjectName("primario")
        bl.addWidget(self.btn_rep)
        pl.addWidget(barra)
        self.nota_rep = QLabel("Cada réplica usa una semilla distinta y varía los tiempos de proceso en ± la variabilidad "
                               "del escenario. Con 0 % de variabilidad el modelo es determinista.")
        self.nota_rep.setWordWrap(True)
        self.nota_rep.setObjectName("tenue")
        pl.addWidget(self.nota_rep)
        cuerpo = FilaAdaptable()
        izq = QVBoxLayout()
        self.tabla_stats = TablaDatos(["Métrica", "n", "Media", "Desv.", "Mín.", "Máx.", "IC 95 % inf.", "IC 95 % sup."],
                                     estirar=0)
        izq.addWidget(self.tabla_stats, 1)
        self.tabla_runs = TablaDatos(["Semilla", "Cierre min", "Lead time", "Completados %", "A tiempo %",
                                     "Espera transp.", "Flota %", "Cola máx."], estirar=None)
        izq.addWidget(self.tabla_runs, 1)
        cuerpo.addLayout(izq, 3)
        der = QFrame(); der.setObjectName("tarjeta")
        dl = QVBoxLayout(der)
        self.estabilidad = Estabilidad()
        dl.addWidget(self.estabilidad)
        dl.addStretch(1)
        cuerpo.addWidget(der, 2)
        pl.addLayout(cuerpo, 1)
        self.tabs.addTab(rep, "Réplicas")

        self.cuerpo.addWidget(self.tabs, 1)
        self.cuerpo.addWidget(self.estado)
        self.btn_simular.clicked.connect(lambda: self.ejecutar_solicitado.emit(0))
        self.btn_rep.clicked.connect(lambda: self.replicas_solicitadas.emit(
            int(self.combo_rep.currentData() or 0), self.n_rep.value()))

    def set_escenarios_replicas(self, opciones: list[tuple]) -> None:
        previo = self.combo_rep.currentData()
        self.combo_rep.clear()
        for i, n in opciones:
            self.combo_rep.addItem(n, i)
        self.combo_rep.setCurrentIndex(max(self.combo_rep.findData(previo), 0))

    def mostrar_resultados(self, resumen, kpis, graf_wip, graf_cola, filas_areas, colores_areas, filas_alertas, colores_alertas):
        self.resumen.setText(resumen)
        for card, (valor, nota) in zip(self.kpis, kpis):
            card.set_valor(valor, nota)
        self.g_wip.set_datos(*graf_wip)
        self.g_cola.set_datos(*graf_cola)
        self.tabla.set_filas(filas_areas, colores=colores_areas)
        self.tabla_alertas.set_filas(filas_alertas, colores=colores_alertas)
        self.tabs.setCurrentIndex(1)

    def mostrar_replicas(self, nota, filas_stats, filas_runs, estabilidad=(), mensaje=""):
        self.nota_rep.setText(nota)
        self.estabilidad.set_datos(estabilidad, mensaje)
        self.tabla_stats.set_filas(filas_stats)
        self.tabla_runs.set_filas(filas_runs)
