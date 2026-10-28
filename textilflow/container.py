# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Raíz de composición: arma los repositorios, los casos de uso y los respaldos, y los entrega juntos en un Contenedor.

from dataclasses import dataclass

from .application.use_cases.alertas import ObtenerAlertas
from .application.use_cases.analisis import (CalcularIndicadores, CompararEscenarios, EjecutarReplicas,
                                             EjecutarSimulacion, ExportarReporte)
from .application.use_cases.inventario import GestionarInventario
from .application.use_cases.cierres import ExportarContingencias, GestionarCierres, InformeCierres
from .application.use_cases.contexto import CargadorContexto
from .application.use_cases.dashboard import ObtenerDashboard
from .application.use_cases.datos import GestionarDatos
from .application.use_cases.demo import CargarDatosDemo
from .application.use_cases.escenarios import GestionarEscenarios
from .application.use_cases.layout import GestionarLayout
from .application.use_cases.parametros import GestionarParametros
from .application.use_cases.procesos import GestionarProcesos
from .application.use_cases.requerimientos import AnalizarRequerimientos
from .application.use_cases.rutas import ConsultarRutasNodo
from .application.use_cases.robots import GestionarRobots
from .application.use_cases.talleres import GestionarTalleres
from .application.use_cases.validacion import ValidarProyecto
from .infrastructure.archive.rlr_archive import RlrArchive
from .infrastructure.excel.openpyxl_gateway import OpenpyxlGateway
from .infrastructure.excel.exportador_reportes import ExportadorReportesArchivo
from .infrastructure.persistence.database import Database
from .infrastructure.persistence import sqlite_repositories as R
from .infrastructure.respaldos import Respaldos
from . import registro


@dataclass
class Contenedor:
    db: Database
    talleres: GestionarTalleres
    layout: GestionarLayout
    procesos: GestionarProcesos
    parametros: GestionarParametros
    robots: GestionarRobots
    escenarios: GestionarEscenarios
    simulacion: EjecutarSimulacion
    replicas: EjecutarReplicas
    requerimientos: AnalizarRequerimientos
    alertas: ObtenerAlertas
    rutas: ConsultarRutasNodo
    indicadores: CalcularIndicadores
    comparacion: CompararEscenarios
    reporte: ExportarReporte
    validacion: ValidarProyecto
    dashboard: ObtenerDashboard
    datos: GestionarDatos
    demo: CargarDatosDemo
    cierres: GestionarCierres
    inventario: GestionarInventario
    informe_cierres: InformeCierres
    exportar_contingencias: ExportarContingencias
    respaldos: Respaldos = None


def construir(ruta_db: str = ":memory:") -> Contenedor:
    db = Database(ruta_db)
    r_taller, r_est, r_con = R.SqliteTallerRepository(db), R.SqliteEstacionRepository(db), R.SqliteConexionRepository(db)
    r_tip, r_rut, r_ped = R.SqliteTipoPrendaRepository(db), R.SqliteRutaProcesoRepository(db), R.SqlitePedidoRepository(db)
    r_rob, r_esc, r_reg = R.SqliteRobotRepository(db), R.SqliteEscenarioRepository(db), R.SqliteRegistroRepository(db)
    r_par, r_cie = R.SqliteParametroRepository(db), R.SqliteCierreRepository(db)

    ctx = CargadorContexto(r_taller, r_est, r_con, r_tip, r_rut, r_ped, r_rob, r_par, r_cie,
                           version=lambda: db.conn.total_changes + 1)
    talleres = GestionarTalleres(r_taller)
    layout = GestionarLayout(r_est, r_con, r_rut)
    procesos = GestionarProcesos(r_tip, r_rut, r_ped, r_est)
    parametros = GestionarParametros(r_par)
    robots = GestionarRobots(r_rob, r_con, r_tip, r_par)
    escenarios = GestionarEscenarios(r_esc, r_est, r_rob)
    simulacion = EjecutarSimulacion(r_esc, r_reg, ctx)
    comparacion = CompararEscenarios(r_esc, r_reg, ctx)
    inventario = GestionarInventario(R.SqliteStockRepository(db), R.SqliteSolicitudCompraRepository(db), r_ped, r_tip,
                                    r_taller)
    alertas = ObtenerAlertas(r_esc, r_reg, ctx, inventario)
    cierres = GestionarCierres(r_cie, r_est)
    informe_cierres = InformeCierres(r_esc, ctx)
    datos = GestionarDatos(talleres, layout, procesos, OpenpyxlGateway(), R.SqliteSnapshotRepository(db), RlrArchive())
    carpeta_resp = None if ruta_db == ":memory:" else registro.carpeta_datos() / "respaldos"
    respaldos = Respaldos(carpeta_resp, datos.exportar_proyecto, datos.restaurar_proyecto)
    return Contenedor(
        db=db, talleres=talleres, layout=layout, procesos=procesos, parametros=parametros, robots=robots,
        escenarios=escenarios, simulacion=simulacion, replicas=EjecutarReplicas(r_esc, ctx),
        requerimientos=AnalizarRequerimientos(r_esc, ctx), alertas=alertas, rutas=ConsultarRutasNodo(),
        indicadores=CalcularIndicadores(r_esc, r_reg), comparacion=comparacion,
        reporte=ExportarReporte(comparacion, ExportadorReportesArchivo()),
        validacion=ValidarProyecto(r_taller, r_est, r_con, r_tip, r_rut, r_ped, r_rob, r_esc, r_reg, r_par),
        dashboard=ObtenerDashboard(r_taller, r_est, r_con, r_tip, r_rut, r_ped, r_esc, r_reg, alertas, ctx),
        datos=datos,
        demo=CargarDatosDemo(talleres, layout, procesos, robots, escenarios, simulacion, parametros, inventario),
        inventario=inventario,
        cierres=cierres, informe_cierres=informe_cierres,
        exportar_contingencias=ExportarContingencias(cierres, informe_cierres, ExportadorReportesArchivo()),
        respaldos=respaldos,
    )
