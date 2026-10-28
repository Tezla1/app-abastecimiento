from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QApplication, QWidget

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


class _Paginas:
    """Lista perezosa de controladores: cada página (vista + controlador) se construye la primera vez que se pide."""

    def __init__(self, fabricas, al_construir):
        self._fabricas = fabricas
        self._hechos = [None] * len(fabricas)
        self._al_construir = al_construir

    def __len__(self):
        return len(self._fabricas)

    def construida(self, i: int) -> bool:
        return self._hechos[i] is not None

    def __getitem__(self, i):
        if self._hechos[i] is None:
            vista, ctl = self._fabricas[i]()
            self._hechos[i] = ctl
            self._al_construir(i, vista)
        return self._hechos[i]

    def __iter__(self):
        for i in range(len(self._fabricas)):
            yield self[i]


class AplicacionController:
    def __init__(self, c: Container, ventana=None):
        self.ctx = AppContext()
        self._c = c
        ctx = self.ctx

        def f(vista_cls, ctl_cls, *args_vista, serv=()):
            def construir():
                vista = vista_cls(*args_vista)
                return vista, ctl_cls(vista, ctx, *[getattr(c, n) for n in serv])
            return construir

        fabricas = [
            f(DashboardView, DashboardController, serv=("dashboard", "layout")),
            f(TallerView, TallerController, ORIGENES_OPC, serv=("talleres",)),
            f(LayoutView, LayoutController, FUNCIONES_OPC, ORIGENES_OPC, serv=("layout", "procesos")),
            f(ModeloView, ModeloController, serv=("escenarios", "indicadores", "simulacion", "parametros")),
            f(RobotView, RobotController, ORIGENES_OPC, serv=("robots",)),
            f(SimulacionView, SimulacionController, TIPOS_OPC, POLITICAS_OPC,
              serv=("escenarios", "layout", "robots", "indicadores", "simulacion", "replicas", "parametros")),
            f(MapaView, MapaController, serv=("escenarios", "layout", "procesos", "simulacion", "rutas")),
            f(RequerimientosView, RequerimientosController, serv=("escenarios", "requerimientos", "alertas", "parametros")),
            f(ComparacionView, ComparacionController, serv=("escenarios", "comparacion")),
            f(ResultadosView, ResultadosController, serv=("escenarios", "comparacion", "reporte")),
            f(ContingenciasView, ContingenciasController, list(MOTIVOS_CIERRE.items()),
              serv=("cierres", "informe_cierres", "exportar_contingencias", "simulacion", "escenarios", "layout")),
            f(ValidacionView, ValidacionController, serv=("validacion",)),
            f(DataManagerView, DataManagerController, serv=("datos", "demo")),
            f(GuiaView, GuiaController),
        ]
        nombres = [
            ("Dashboard", theme.AZUL), ("Caracterización del taller", theme.NARANJA),
            ("Layout y movimientos", theme.AZUL), ("Modelo matemático", theme.VERDE),
            ("Diseño conceptual del robot", theme.TURQUESA), ("Escenarios y simulación", theme.VERDE),
            ("Mapa operativo", theme.VERDE), ("Requerimientos y normativas", theme.DORADO),
            ("Comparación experimental", theme.MORADO), ("Resultados y reportes", theme.NARANJA),
            ("Contingencias y cierres", theme.ROJO), ("Validación integral", theme.DORADO),
            ("Data Manager", theme.TURQUESA), ("Guía y acerca de", theme.TURQUESA),
        ]
        self._indice_req = [n for n, _ in nombres].index("Requerimientos y normativas")
        self.ventana = None
        self.controladores = _Paginas(fabricas, self._pagina_lista)
        paginas = [(n, col, QWidget()) for n, col in nombres]
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

    def _pagina_lista(self, i: int, vista) -> None:
        """Pone la vista recién construida en el lugar de su marcador."""
        if self.ventana is not None:
            self.ventana.poner_pagina(i, vista)

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
        if ventana is not None and self.controlador is not None:
            # se libera primero el contenido anterior para que reaplicar los estilos sea barato
            self.controlador.ventana.vaciar()
            self.controlador.ctx.deleteLater()
        self._qapp.setStyleSheet(theme.hoja_de_estilo())
        self.controlador = AplicacionController(self._c, ventana)
        v = self.controlador.ventana
        v.tema_solicitado.connect(self.alternar_tema)
        if pagina:
            v.seleccionar(pagina)
        self.controlador.iniciar(taller_id)

    def alternar_tema(self) -> None:
        """Cambia el tema sin construir de nuevo las 14 páginas: la ventana conserva su marco y solo se
        vuelve a crear la página visible; las demás se construyen al visitarlas (ya con la paleta nueva)."""
        viejo = self.controlador
        v = viejo.ventana
        taller, pagina = viejo.ctx.taller_id, v.pagina_actual()
        nuevo = "claro" if theme.tema_actual() == "oscuro" else "oscuro"
        self._ajustes.setValue("tema", nuevo)
        theme.aplicar(nuevo)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        v.setUpdatesEnabled(False)
        try:
            self._montar(taller, pagina, v)
        finally:
            v.setUpdatesEnabled(True)
            QApplication.restoreOverrideCursor()
