# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Une la ventana con los controladores. Crea las páginas solo cuando se visitan por primera vez,
# cambia el tema, guarda al cerrar, hace el respaldo cada 5 minutos y mantiene al día la insignia de alertas.

import os
from datetime import datetime

from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget

from .. import registro
from . import tareas
from ..container import Contenedor
from . import theme
from .context import ContextoApp
from ..domain.entities import MOTIVOS_CIERRE, POLITICAS
from .controllers.base import COMPRAS_OPC, FUNCIONES_OPC, ORIGENES_OPC, TIPOS_OPC
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
from .ventana_principal import VentanaPrincipal
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
    def __init__(self, c: Contenedor, ventana=None):
        self.ctx = ContextoApp()
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
            f(LayoutView, LayoutController, FUNCIONES_OPC, ORIGENES_OPC, COMPRAS_OPC,
              serv=("layout", "procesos", "inventario")),
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
            f(DataManagerView, DataManagerController, serv=("datos", "demo", "respaldos")),
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
            self.ventana = VentanaPrincipal(paginas)
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
        self._temporizador_alertas = QTimer(self.ventana)
        self._temporizador_alertas.setSingleShot(True)
        self._temporizador_alertas.setInterval(250 if not os.environ.get("TEXTILFLOW_SINCRONO") else 0)
        self._temporizador_alertas.timeout.connect(self._actualizar_alertas)
        self.ctx.alertas_obsoletas.connect(self._temporizador_alertas.start)
        self.ctx.taller_activo_cambiado.connect(self._taller_cambio)
        self.ctx.talleres_cambiaron.connect(self._recargar_talleres)

    def _pagina_lista(self, i: int, vista) -> None:
        if self.ventana is not None:
            self.ventana.poner_pagina(i, vista)

    def _pagina_cambio(self, i: int) -> None:
        self.controladores[i].refrescar()
        self._actualizar_alertas()

    def iniciar(self, taller_id=None) -> None:
        talleres = self._c.talleres.listar()
        self.ctx.taller_id = taller_id if taller_id in {t.id for t in talleres} else (talleres[0].id if talleres else None)
        self._recargar_talleres()

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
        except Exception as exc:
            registro.registrar("No se pudieron calcular las alertas del taller activo", exc)
            alertas = []
        self.ventana.set_alertas(len(alertas), sum(a.nivel == "CRÍTICA" for a in alertas),
                                 sum(a.nivel == "ALTA" for a in alertas))


class Aplicacion:
    def __init__(self, c: Contenedor, qapp):
        self._c, self._qapp = c, qapp
        self._ajustes = QSettings("TextilFlow", "TextilFlow")
        theme.aplicar(str(self._ajustes.value("tema", "oscuro")))
        self.controlador = None
        self._montar(diferir=not tareas.SINCRONO)
        self.controlador.ventana.antes_de_cerrar = self._antes_de_cerrar
        self._cambios_en_respaldo = 0
        self._timer_respaldo = QTimer()
        self._timer_respaldo.setInterval(5 * 60 * 1000)
        self._timer_respaldo.timeout.connect(self.respaldar_si_hay_cambios)
        if c.respaldos is not None and c.respaldos.activo:
            self._timer_respaldo.start()
            lista = c.respaldos.listar()
            if not lista or (datetime.now() - lista[0][1]).total_seconds() > 3600:
                try:
                    c.respaldos.crear()
                except Exception as e:
                    registro.registrar("No se pudo crear el respaldo inicial", e)
        self.controlador.ventana.show()

    def respaldar_si_hay_cambios(self) -> None:
        r = self._c.respaldos
        if r is None or not r.activo or tareas.hay_tarea_activa():
            return
        total = self._c.db.conn.total_changes
        if total == self._cambios_en_respaldo:
            return
        try:
            r.crear()
            self._cambios_en_respaldo = total
        except Exception as e:
            registro.registrar("No se pudo crear el respaldo automático", e)

    def _antes_de_cerrar(self) -> bool:
        v = self.controlador.ventana
        if self._c.db.cambios_sin_guardar() > 0:
            caja = QMessageBox(v)
            caja.setIcon(QMessageBox.Icon.Question)
            caja.setWindowTitle("TextilFlow")
            caja.setText("<b>¿Guardar el proyecto antes de salir?</b>")
            caja.setInformativeText("Hizo cambios desde la última vez que guardó (o desde que abrió el programa). "
                                    "«Guardar como…» crea un archivo .rlr con el nombre que elija.<br><br>"
                                    "<i>Sus datos también quedan guardados automáticamente dentro de TextilFlow y en los "
                                    "respaldos automáticos; el archivo con nombre sirve para llevarlo a otro equipo o "
                                    "volver a este punto.</i>")
            guardar = caja.addButton("Guardar como…", QMessageBox.ButtonRole.AcceptRole)
            caja.addButton("No guardar", QMessageBox.ButtonRole.DestructiveRole)
            cancelar = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            caja.setDefaultButton(guardar)
            caja.setEscapeButton(cancelar)
            caja.exec()
            b = caja.clickedButton()
            if b is cancelar:
                return False
            if b is guardar and not self._guardar_proyecto(v):
                return False
        self.respaldar_si_hay_cambios()
        return True

    def _guardar_proyecto(self, ventana) -> bool:
        ruta, _ = QFileDialog.getSaveFileName(ventana, "Guardar proyecto", f"proyecto_{datetime.now():%Y-%m-%d}.rlr",
                                              "Proyecto TextilFlow (*.rlr)")
        if not ruta:
            return False
        if not ruta.lower().endswith(".rlr"):
            ruta += ".rlr"
        try:
            self._c.datos.exportar_proyecto(ruta)
        except Exception as e:
            registro.registrar("No se pudo guardar el proyecto al cerrar", e)
            d = registro.describir(type(e), e, e.__traceback__)
            QMessageBox.warning(ventana, "No se pudo guardar", f"{d['titulo']}: {d['que']}\n{d['resumen']}")
            return False
        self._c.db.marcar_guardado()
        return True

    def _montar(self, taller_id=None, pagina: int = 0, ventana=None, diferir: bool = False) -> None:
        if ventana is not None and self.controlador is not None:
            self.controlador.ventana.vaciar()
            self.controlador.ctx.deleteLater()
        self._qapp.setStyleSheet(theme.hoja_de_estilo())
        self.controlador = AplicacionController(self._c, ventana)
        v = self.controlador.ventana
        v.tema_solicitado.connect(self.alternar_tema)
        if pagina:
            v.seleccionar(pagina)
        if diferir:
            v.estado.setText("● CARGANDO…")
            ctl = self.controlador

            def cargar() -> None:
                if self.controlador is ctl:
                    ctl.iniciar(taller_id)
                    v.estado.setText("● READY")
            QTimer.singleShot(0, cargar)
        else:
            self.controlador.iniciar(taller_id)

    def alternar_tema(self) -> None:
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
