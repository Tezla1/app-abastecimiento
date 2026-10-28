import math
from typing import Optional

from ...domain import analisis, normativa
from ...domain.entities import Escenario
from ..dto import FilaBarrido, Requerimientos
from ..errors import ErrorDeNegocio
from ..progreso import Progreso, avisar
from ..ports import EscenarioRepository
from .contexto import CargadorContexto
from .nucleo import analizar, correr, exigir_simulable


def viajes_por_prenda(ctx, esc: Escenario) -> list[dict]:
    lotes_por_tipo: dict[int, int] = {}
    unidades: dict[int, int] = {}
    for p in ctx.pedidos:
        t = next((x for x in ctx.tipos if x.id == p.tipo_prenda_id), None)
        if not t:
            continue
        n_lotes = math.ceil(p.cantidad * esc.factor_demanda_pct / 100.0 / t.unidades_por_lote)
        lotes_por_tipo[t.id] = lotes_por_tipo.get(t.id, 0) + n_lotes
        unidades[t.id] = unidades.get(t.id, 0) + p.cantidad
    ramas = {}
    for r in ctx.rutas:
        ramas.setdefault(r.tipo_prenda_id, []).append(r)
    out = []
    for t in ctx.tipos:
        if t.id not in lotes_por_tipo:
            continue
        por_viaje = int(esc.capacidad_kg // t.peso_unidad_kg)
        viaje_lote = math.ceil(t.unidades_por_lote / por_viaje) if por_viaje else None
        traslados = max((len(r.pasos()) - 1 for r in ramas.get(t.id, [])), default=0)
        out.append({
            "prenda": t.nombre, "peso_unidad_kg": t.peso_unidad_kg, "lote_u": t.unidades_por_lote,
            "lote_kg": t.peso_unidad_kg * t.unidades_por_lote, "unidades_por_viaje": por_viaje,
            "viajes_por_traslado": viaje_lote, "lotes": lotes_por_tipo[t.id], "unidades": unidades[t.id],
            "traslados_por_lote": traslados,
            "viajes_estimados": (viaje_lote * traslados * lotes_por_tipo[t.id]) if viaje_lote else None})
    return out


class AnalizarRequerimientos:
    def __init__(self, escenarios: EscenarioRepository, ctx: CargadorContexto):
        self._esc, self._ctx = escenarios, ctx

    def execute(self, escenario_id: int, max_recursos: int = 6, progreso: Progreso = None) -> Requerimientos:
        esc = self._esc.get(escenario_id)
        if esc is None:
            raise ErrorDeNegocio("Seleccione un escenario guardado.")
        ctx = self._ctx.cargar(esc.taller_id)
        exigir_simulable(ctx)
        par = ctx.par
        base = analizar(ctx, esc, correr(ctx, esc))
        escenarios = self._esc.list_by_taller(esc.taller_id)
        cumpl = normativa.evaluar(par, ctx.taller, ctx.estaciones, ctx.conexiones, escenarios, ctx.robots)
        criticos = analisis.componentes_criticos(
            ctx.estaciones, ctx.conexiones, base.estados, base.trafico,
            par["ancho_min_pasillo_m"], par["umbral_cuello_botella_pct"])
        robot = ctx.robot_de(esc)
        ancho = normativa.ancho_requerido_robot(robot, par) if robot else 0.0
        ramas = analisis.distancias_ramas(ctx.estaciones, ctx.conexiones, ctx.tipos, ctx.rutas,
                                          esc.velocidad_ms, ancho, ctx.cerrados(), ctx.sin_paso())
        barrido = self._barrido(ctx, esc, max(1, min(max_recursos, 12)), progreso)
        objetivo = par["utilizacion_objetivo_flota_pct"]
        mejor_cierre = min((f.makespan_min for f in barrido), default=0)
        mejor_comp = max((f.completados_pct for f in barrido), default=0)
        for f in barrido:
            f.cumple = ((f.utilizacion_pct is None or f.utilizacion_pct <= objetivo)
                        and f.completados_pct >= mejor_comp - 1e-9 and f.makespan_min <= mejor_cierre * 1.02)
        recomendado = next((f.recursos for f in barrido if f.cumple), None)
        notas = []
        if recomendado is None:
            notas.append(f"Ningún tamaño de flota entre 1 y {len(barrido)} cumple el objetivo de utilización "
                         f"({objetivo:g} %) con el máximo de lotes completados: el límite no es el transporte.")
        cuello = analisis.cuello_de_botella(base.estados, par["umbral_cuello_botella_pct"])
        if cuello and mejor_comp < 100:
            notas.append(f"Aunque haya más equipos, el trabajo no termina por el cuello de botella en "
                         f"{cuello.nombre or cuello.codigo}: agregar puestos allí rinde más que agregar equipos.")
        return Requerimientos(esc, criticos, ramas, base.recorridos, base.flota, barrido, recomendado,
                              viajes_por_prenda(ctx, esc), cumpl, base.estados, notas)

    @staticmethod
    def _barrido(ctx, esc: Escenario, nmax: int, progreso: Progreso = None) -> list[FilaBarrido]:
        out = []
        for n in range(1, nmax + 1):
            avisar(progreso, n - 1, nmax, f"Probando una flota de {n} equipo(s) de {nmax}")
            res = correr(ctx, esc, num_recursos=n)
            r = analizar(ctx, replace_n(esc, n), res)
            out.append(FilaBarrido(n, r.indicadores.get("utilizacion_pct"), r.indicadores.get("espera_prom"),
                                   r.ind.completados_pct, r.ind.lead_time_prom_min, r.ind.makespan_min,
                                   r.ind.pedidos_a_tiempo_pct))
        return out


def replace_n(esc: Escenario, n: int) -> Escenario:
    from dataclasses import replace
    return replace(esc, num_recursos=n)
