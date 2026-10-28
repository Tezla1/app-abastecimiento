import math
from collections import OrderedDict
from dataclasses import dataclass, field, replace
from typing import Optional

from ...domain import analisis, calculos, normativa
from ...domain.alertas import alertas_cierres, alertas_escenario, ordenar
from ...domain.entities import (MOTIVOS_CIERRE, Conexion, Escenario, Estacion, Parametro, Pedido, Registro, Robot,
                                RutaProceso, Taller, TipoPrenda)
from ...domain.simulacion import CierreSim, ParametrosSimulacion, simular
from ..dto import ResultadoSimulacion
from ..errors import ErrorDeNegocio


@dataclass
class Contexto:
    taller: Taller
    estaciones: list = field(default_factory=list)
    conexiones: list = field(default_factory=list)
    tipos: list = field(default_factory=list)
    rutas: list = field(default_factory=list)
    pedidos: list = field(default_factory=list)
    robots: list = field(default_factory=list)
    par: dict = field(default_factory=dict)
    cierres: list = field(default_factory=list)
    version: int = 0          # versión de los datos (cambia con cada escritura en la base); 0 = no usar caché

    def vigentes(self) -> list:
        return [c for c in self.cierres if c.vigente]

    def cerrados(self) -> frozenset:
        return frozenset(c.codigo for c in self.vigentes())

    def sin_paso(self) -> frozenset:
        return frozenset(c.codigo for c in self.vigentes() if c.bloquea_paso)

    def sin_cierres(self) -> "Contexto":
        return replace(self, cierres=[])

    def estaciones_efectivas(self) -> list:
        fijos = {c.codigo for c in self.vigentes() if c.desde_min <= 0 and not c.hasta_min}
        return [replace(e, grupo="") if e.codigo in fijos else e for e in self.estaciones]

    def robot_de(self, esc: Escenario) -> Optional[Robot]:
        return next((r for r in self.robots if r.id == esc.robot_id), None) if esc.robot_id else None

    def prendas_por_pedido(self) -> dict:
        nombres = {t.id: t.nombre for t in self.tipos}
        return {p.id: nombres.get(p.tipo_prenda_id, "?") for p in self.pedidos}


def parametros_simulacion(ctx: Contexto, esc: Escenario, semilla: Optional[int] = None,
                          num_recursos: Optional[int] = None) -> ParametrosSimulacion:
    robot = ctx.robot_de(esc)
    ancho = normativa.ancho_requerido_robot(robot, ctx.par) if robot else 0.0
    return ParametrosSimulacion(
        num_recursos=num_recursos or esc.num_recursos, velocidad_ms=esc.velocidad_ms,
        capacidad_kg=esc.capacidad_kg, t_carga_s=esc.t_carga_s, t_descarga_s=esc.t_descarga_s,
        nodo_inicial=esc.nodo_inicial, reposicionamiento=esc.reposicionamiento,
        ancho_requerido_m=ancho, tiempo_observacion_min=esc.tiempo_observacion_min,
        politica=esc.politica, balanceo=esc.balanceo, factor_demanda_pct=esc.factor_demanda_pct,
        variabilidad_pct=esc.variabilidad_pct, semilla=esc.semilla if semilla is None else semilla,
        cierres=tuple(CierreSim(c.codigo, c.desde_min, c.hasta_min if c.hasta_min else math.inf, c.bloquea_paso,
                                MOTIVOS_CIERRE.get(c.motivo, c.motivo)) for c in ctx.vigentes()))


def exigir_simulable(ctx: Contexto) -> None:
    if not ctx.conexiones:
        raise ErrorDeNegocio("El taller no tiene conexiones registradas.")
    if not ctx.pedidos:
        raise ErrorDeNegocio("El taller no tiene pedidos que simular.")
    if not ctx.rutas:
        raise ErrorDeNegocio("No hay rutas de proceso definidas (pestaña «Prendas y rutas»).")


def correr(ctx: Contexto, esc: Escenario, semilla: Optional[int] = None,
           num_recursos: Optional[int] = None):
    p = parametros_simulacion(ctx, esc, semilla, num_recursos)
    return simular(p, ctx.estaciones, ctx.conexiones, ctx.tipos, ctx.rutas, ctx.pedidos)


def registros_de(esc_id: int, res) -> list[Registro]:
    return [Registro(esc_id, t.pedido_id, t.lote, t.desde, t.hacia, t.atendida, t.espera_min,
                     t.recorrido_min, t.distancia_m, t.inicio_min, t.fin_min, t.recurso, t.viajes,
                     t.detalle) for t in res.tareas]


def calc_de(esc: Escenario, registros: list, num_recursos: Optional[int] = None) -> dict:
    e = esc.para_calculo()
    if num_recursos:
        e["num_recursos"] = num_recursos
    return calculos.calcular_indicadores(e, [r.para_calculo() for r in registros])


def analizar(ctx: Contexto, esc: Escenario, res) -> ResultadoSimulacion:
    registros = registros_de(esc.id, res)
    calc = calc_de(esc, registros)
    carga = analisis.carga_ofrecida(ctx.estaciones_efectivas(), ctx.tipos, ctx.rutas, ctx.pedidos,
                                    esc.tiempo_observacion_min, esc.factor_demanda_pct)
    estados = analisis.analizar_estaciones(res, ctx.estaciones, carga)
    ind = analisis.indicadores_proceso(res, ctx.pedidos)
    prendas = ctx.prendas_por_pedido()
    traf = analisis.trafico(res)
    alertas = ordenar(alertas_cierres(ctx.cierres, ctx.estaciones)
                      + alertas_escenario(ctx.par, esc, res, estados, ind, calc, ctx.pedidos, prendas,
                                          ctx.estaciones, traf))
    return ResultadoSimulacion(
        esc, res, registros, calc, ind, estados, carga, traf,
        analisis.series_tiempo(res, ctx.estaciones), alertas,
        analisis.flota_analitica(res, ctx.par["utilizacion_objetivo_flota_pct"]),
        analisis.resumen_recorridos(res), prendas)


_CACHE: "OrderedDict" = OrderedDict()
_CACHE_MAX = 16


def _clave(ctx: Contexto, esc: Escenario):
    cierres = tuple((c.codigo, c.vigente, c.desde_min, c.hasta_min, c.bloquea_paso) for c in ctx.cierres)
    return ctx.version, ctx.taller.id, repr(esc), cierres


def simular_completo(ctx: Contexto, esc: Escenario) -> ResultadoSimulacion:
    """Simula y analiza un escenario. El resultado se guarda en una caché pequeña mientras los datos no cambien:
    el Dashboard, las alertas y el mapa piden el mismo escenario varias veces y no hace falta repetir la simulación."""
    exigir_simulable(ctx)
    if not ctx.version:
        return analizar(ctx, esc, correr(ctx, esc))
    k = _clave(ctx, esc)
    if k in _CACHE:
        _CACHE.move_to_end(k)
        return _CACHE[k]
    r = analizar(ctx, esc, correr(ctx, esc))
    _CACHE[k] = r
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return r
