"""Raíz de composición: el único lugar que conoce las implementaciones concretas."""
from dataclasses import dataclass

from .application.use_cases.alertas import ObtenerAlertas
from .application.use_cases.analisis import (CalcularIndicadores, CompararEscenarios, EjecutarReplicas,
                                             EjecutarSimulacion, ExportarReporte)
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
from .infrastructure.excel.report_exporter import ArchivoReportExporter
from .infrastructure.persistence.database import Database
from .infrastructure.persistence import sqlite_repositories as R


@dataclass
class Container:
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


def construir(ruta_db: str = ":memory:") -> Container:
    db = Database(ruta_db)
    r_taller, r_est, r_con = R.SqliteTallerRepository(db), R.SqliteEstacionRepository(db), R.SqliteConexionRepository(db)
    r_tip, r_rut, r_ped = R.SqliteTipoPrendaRepository(db), R.SqliteRutaProcesoRepository(db), R.SqlitePedidoRepository(db)
    r_rob, r_esc, r_reg = R.SqliteRobotRepository(db), R.SqliteEscenarioRepository(db), R.SqliteRegistroRepository(db)
    r_par = R.SqliteParametroRepository(db)

    ctx = CargadorContexto(r_taller, r_est, r_con, r_tip, r_rut, r_ped, r_rob, r_par)
    talleres = GestionarTalleres(r_taller)
    layout = GestionarLayout(r_est, r_con, r_rut)
    procesos = GestionarProcesos(r_tip, r_rut, r_ped, r_est)
    parametros = GestionarParametros(r_par)
    robots = GestionarRobots(r_rob, r_con, r_tip, r_par)
    escenarios = GestionarEscenarios(r_esc, r_est, r_rob)
    simulacion = EjecutarSimulacion(r_esc, r_reg, ctx)
    comparacion = CompararEscenarios(r_esc, r_reg, ctx)
    alertas = ObtenerAlertas(r_esc, r_reg, ctx)
    return Container(
        db=db, talleres=talleres, layout=layout, procesos=procesos, parametros=parametros, robots=robots,
        escenarios=escenarios, simulacion=simulacion, replicas=EjecutarReplicas(r_esc, ctx),
        requerimientos=AnalizarRequerimientos(r_esc, ctx), alertas=alertas, rutas=ConsultarRutasNodo(),
        indicadores=CalcularIndicadores(r_esc, r_reg), comparacion=comparacion,
        reporte=ExportarReporte(comparacion, ArchivoReportExporter()),
        validacion=ValidarProyecto(r_taller, r_est, r_con, r_tip, r_rut, r_ped, r_rob, r_esc, r_reg, r_par),
        dashboard=ObtenerDashboard(r_taller, r_est, r_con, r_tip, r_rut, r_ped, r_esc, r_reg, alertas, ctx),
        datos=GestionarDatos(talleres, layout, procesos, OpenpyxlGateway(), R.SqliteSnapshotRepository(db), RlrArchive()),
        demo=CargarDatosDemo(talleres, layout, procesos, robots, escenarios, simulacion, parametros),
    )
