from PyQt6.QtCore import QSettings

from ..container import Container
from . import theme
from .context import AppContext
from ..domain.entities import MOTIVOS_CIERRE, POLITICAS
from .controllers.base import FUNCIONES_OPC, ORIGENES_OPC, TIPOS_OPC
from .controllers.comparacion_controller import ComparacionController
from .controllers.contingencias_controller import ContingenciasController
from .controllers.dashboard_controller import DashboardController
from .controllers.data_manager_controller import DataManagerController
from .controllers.guia_controller import GuiaController
from .controllers.layout_controller import LayoutController
from .controllers.mapa_controller import MapaController
from .controllers.requerimientos_controller import RequerimientosController
from .controllers.modelo_controller import ModeloController
from .controllers.resultados_controller import ResultadosController
from .controllers.robot_controller import RobotController
from .controllers.simulacion_controller import SimulacionController
from .controllers.taller_controller import TallerController
from .controllers.validacion_controller import ValidacionController
from .main_window import MainWindow
from .views.comparacion_view import ComparacionView
from .views.contingencias_view import ContingenciasView
from .views.dashboard_view import DashboardView
from .views.data_manager_view import DataManagerView
from .views.guia_view import GuiaView
from .views.layout_view import LayoutView
from .views.mapa_view import MapaView
from .views.requerimientos_view import RequerimientosView
from .views.modelo_view import ModeloView
from .views.resultados_view import ResultadosView
from .views.robot_view import RobotView
from .views.simulacion_view import SimulacionView
from .views.taller_view import TallerView
from .views.validacion_view import ValidacionView

POLITICAS_OPC = list(POLITICAS.items())


class AplicacionController:
    def __init__(self, c: Container, ventana=None):
        self.ctx = AppContext()
        self._c = c
        v = {
            "dashboard": DashboardView(), "taller": TallerView(ORIGENES_OPC),
            "layout": LayoutView(FUNCIONES_OPC, ORIGENES_OPC), "modelo": ModeloView(),
            "robot": RobotView(ORIGENES_OPC), "simulacion": SimulacionView(TIPOS_OPC, POLITICAS_OPC),
            "mapa": MapaView(), "req": RequerimientosView(), "guia": GuiaView(),
            "comparacion": ComparacionView(), "resultados": ResultadosView(),
            "validacion": ValidacionView(), "cont": ContingenciasView(list(MOTIVOS_CIERRE.items())), "datos": DataManagerView(),
        }
        self.controladores = [
            DashboardController(v["dashboard"], self.ctx, c.dashboard, c.layout),
            TallerController(v["taller"], self.ctx, c.talleres),
            LayoutController(v["layout"], self.ctx, c.layout, c.procesos),
            ModeloController(v["modelo"], self.ctx, c.escenarios, c.indicadores, c.simulacion, c.parametros),
            RobotController(v["robot"], self.ctx, c.robots),
            SimulacionController(v["simulacion"], self.ctx, c.escenarios, c.layout, c.robots, c.indicadores, c.simulacion,
                                 c.replicas, c.parametros),
            MapaController(v["mapa"], self.ctx, c.escenarios, c.layout, c.procesos, c.simulacion, c.rutas),
            RequerimientosController(v["req"], self.ctx, c.escenarios, c.requerimientos, c.alertas, c.parametros),
            ComparacionController(v["comparacion"], self.ctx, c.escenarios, c.comparacion),
            ResultadosController(v["resultados"], self.ctx, c.escenarios, c.comparacion, c.reporte),
            ContingenciasController(v["cont"], self.ctx, c.cierres, c.informe_cierres, c.simulacion, c.escenarios, c.layout),
            ValidacionController(v["validacion"], self.ctx, c.validacion),
            DataManagerController(v["datos"], self.ctx, c.datos, c.demo),
            GuiaController(v["guia"], self.ctx),
        ]
        paginas = [
            ("Dashboard", theme.AZUL, v["dashboard"]),
            ("Caracterización del taller", theme.NARANJA, v["taller"]),
            ("Layout y movimientos", theme.AZUL, v["layout"]),
            ("Modelo matemático", theme.VERDE, v["modelo"]),
            ("Diseño conceptual del robot", theme.TURQUESA, v["robot"]),
            ("Escenarios y simulación", theme.VERDE, v["simulacion"]),
            ("Mapa operativo", theme.VERDE, v["mapa"]),
            ("Requerimientos y normativas", theme.DORADO, v["req"]),
            ("Comparación experimental", theme.MORADO, v["comparacion"]),
            ("Resultados y reportes", theme.NARANJA, v["resultados"]),
            ("Contingencias y cierres", theme.ROJO, v["cont"]),
            ("Validación integral", theme.DORADO, v["validacion"]),
            ("Data Manager", theme.TURQUESA, v["datos"]),
            ("Guía y acerca de", theme.TURQUESA, v["guia"]),
        ]
        self._indice_req = [n for n, *_ in paginas].index("Requerimientos y normativas")
        if ventana is None:
            self.ventana = MainWindow(paginas)
        else:
            for senal in (ventana.pagina_cambiada, ventana.taller_elegido, ventana.alertas_solicitadas, ventana.tema_solicitado):
                senal.disconnect()
            ventana.armar(paginas)
            self.ventana = ventana
        self.ventana.pagina_cambiada.connect(self._pagina_cambio)
        self.ventana.taller_elegido.connect(self.ctx.activar)
        self.ventana.alertas_solicitadas.connect(lambda: self.ventana.ir_a(self._indice_req))
        self.ctx.proveedor_cerrados = c.cierres.cerrados
        self.ctx.cierres_cambiaron.connect(self._actualizar_alertas)
        self.ctx.taller_activo_cambiado.connect(self._taller_cambio)
        self.ctx.talleres_cambiaron.connect(self._recargar_talleres)

    def _pagina_cambio(self, i: int) -> None:
        self.controladores[i].refrescar()
        self._actualizar_alertas()

    def iniciar(self, taller_id=None) -> None:
        talleres = self._c.talleres.listar()
        self.ctx.taller_id = taller_id if taller_id in {t.id for t in talleres} else (talleres[0].id if talleres else None)
        self._recargar_talleres()
        self._refrescar_actual()

    def _recargar_talleres(self) -> None:
        talleres = self._c.talleres.listar()
        ids = {t.id for t in talleres}
        if self.ctx.taller_id not in ids:
            self.ctx.taller_id = talleres[0].id if talleres else None
        self.ventana.set_talleres([(t.id, t.nombre) for t in talleres], self.ctx.taller_id)
        self._refrescar_actual()

    def _taller_cambio(self) -> None:
        self.ventana.set_talleres([(t.id, t.nombre) for t in self._c.talleres.listar()], self.ctx.taller_id)
        self._refrescar_actual()

    def _refrescar_actual(self) -> None:
        self.controladores[self.ventana.pagina_actual()].refrescar()
        self._actualizar_alertas()

    def _actualizar_alertas(self) -> None:
        tid = self.ctx.taller_id
        try:
            alertas = self._c.alertas.execute(tid) if tid else []
        except Exception:
            alertas = []
        self.ventana.set_alertas(len(alertas), sum(a.nivel == "CRÍTICA" for a in alertas),
                                 sum(a.nivel == "ALTA" for a in alertas))


class Aplicacion:
    def __init__(self, c: Container, qapp):
        self._c, self._qapp = c, qapp
        self._ajustes = QSettings("TextilFlow", "TextilFlow")
        theme.aplicar(str(self._ajustes.value("tema", "oscuro")))
        self.controlador = None
        self._montar()
        self.controlador.ventana.show()

    def _montar(self, taller_id=None, pagina: int = 0, ventana=None) -> None:
        self._qapp.setStyleSheet(theme.hoja_de_estilo())
        self.controlador = AplicacionController(self._c, ventana)
        v = self.controlador.ventana
        v.tema_solicitado.connect(self.alternar_tema)
        self.controlador.iniciar(taller_id)
        if pagina:
            v.ir_a(pagina)

    def alternar_tema(self) -> None:
        viejo = self.controlador
        nuevo = "claro" if theme.tema_actual() == "oscuro" else "oscuro"
        self._ajustes.setValue("tema", nuevo)
        theme.aplicar(nuevo)
        self._montar(viejo.ctx.taller_id, viejo.ventana.pagina_actual(), viejo.ventana)
