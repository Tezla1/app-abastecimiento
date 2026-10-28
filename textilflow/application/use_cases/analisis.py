import copy
from dataclasses import replace

from ...domain import calculos, estadistica
from ...domain.analisis import analizar_estaciones, indicadores_proceso, series_tiempo
from ..dto import (DetalleIndicadores, ResultadoComparacion, ResultadoReplicas, ResultadoSimulacion)
from ..errors import ErrorDeNegocio
from ..progreso import Progreso, avisar
from ..ports import EscenarioRepository, RegistroRepository, ExportadorReportes
from .contexto import CargadorContexto
from .nucleo import analizar, calc_de, correr, exigir_simulable, simular_completo

METRICAS = {
    "makespan_min": ("Cierre de la última entrega (min)", 1),
    "lead_time_min": ("Lead time medio por lote (min)", 1),
    "completados_pct": ("Lotes completados (%)", 1),
    "a_tiempo_pct": ("Pedidos a tiempo (%)", 1),
    "espera_traslado_min": ("Espera media por transporte (min)", 2),
    "utilizacion_flota_pct": ("Utilización de la flota (%)", 1),
    "cola_max": ("Cola máxima en una estación (lotes)", 0),
}


class EjecutarSimulacion:
    def __init__(self, escenarios: EscenarioRepository, registros: RegistroRepository, ctx: CargadorContexto):
        self._esc, self._reg, self._ctx = escenarios, registros, ctx

    def execute(self, escenario_id: int, guardar: bool = True) -> ResultadoSimulacion:
        esc = self._esc.get(escenario_id)
        if esc is None:
            raise ErrorDeNegocio("Seleccione un escenario guardado para simular.")
        r = simular_completo(self._ctx.cargar(esc.taller_id), esc)
        if guardar:
            r = copy.copy(r)
            self._reg.replace_for_escenario(esc.id, r.registros)
            r.registros = self._reg.list_by_escenario(esc.id)
            r.indicadores = calc_de(esc, r.registros)
        return r


class CalcularIndicadores:
    def __init__(self, escenarios: EscenarioRepository, registros: RegistroRepository):
        self._esc, self._reg = escenarios, registros

    def execute(self, escenario_id: int) -> DetalleIndicadores:
        esc = self._esc.get(escenario_id)
        if esc is None:
            raise ErrorDeNegocio("Seleccione un escenario.")
        regs = self._reg.list_by_escenario(escenario_id)
        return DetalleIndicadores(esc, regs, calc_de(esc, regs))


class EjecutarReplicas:

    def __init__(self, escenarios: EscenarioRepository, ctx: CargadorContexto):
        self._esc, self._ctx = escenarios, ctx

    def execute(self, escenario_id: int, n: int, progreso: Progreso = None) -> ResultadoReplicas:
        esc = self._esc.get(escenario_id)
        if esc is None:
            raise ErrorDeNegocio("Seleccione un escenario guardado.")
        if not 2 <= n <= 500:
            raise ErrorDeNegocio("El número de réplicas debe estar entre 2 y 500.")
        ctx = self._ctx.cargar(esc.taller_id)
        exigir_simulable(ctx)
        filas = []
        for i in range(n):
            avisar(progreso, i, n, f"Réplica {i + 1} de {n}")
            semilla = esc.semilla + i
            res = correr(ctx, esc, semilla)
            regs = [t for t in res.tareas]
            ind = indicadores_proceso(res, ctx.pedidos)
            calc = calc_de(esc, [_a_registro(t) for t in regs])
            estados = analizar_estaciones(res, ctx.estaciones)
            filas.append({
                "semilla": semilla, "makespan_min": ind.makespan_min, "lead_time_min": ind.lead_time_prom_min,
                "completados_pct": ind.completados_pct, "a_tiempo_pct": ind.pedidos_a_tiempo_pct,
                "espera_traslado_min": calc.get("espera_prom"), "utilizacion_flota_pct": calc.get("utilizacion_pct"),
                "cola_max": max((e.cola_max for e in estados), default=0)})
        resumen = {k: estadistica.resumir([f[k] for f in filas]) for k in METRICAS}
        nota = ""
        if esc.variabilidad_pct <= 0:
            nota = ("La variabilidad del escenario es 0 %: todas las réplicas son idénticas (modelo determinista). "
                    "Defina una variabilidad > 0 % en «Condiciones base» para estimar la dispersión.")
        return ResultadoReplicas(esc, n, filas, resumen, nota)


def _a_registro(t):
    from ...domain.entities import Registro
    return Registro(0, t.pedido_id, t.lote, t.desde, t.hacia, t.atendida, t.espera_min, t.recorrido_min,
                    t.distancia_m, t.inicio_min, t.fin_min, t.recurso, t.viajes, t.detalle)


class CompararEscenarios:
    def __init__(self, escenarios: EscenarioRepository, registros: RegistroRepository, ctx: CargadorContexto):
        self._esc, self._reg, self._ctx = escenarios, registros, ctx

    def execute(self, base_id: int, alternativo_id: int) -> ResultadoComparacion:
        if base_id == alternativo_id:
            raise ErrorDeNegocio("Elija dos escenarios distintos para comparar.")
        base, alt = self._esc.get(base_id), self._esc.get(alternativo_id)
        if base is None or alt is None:
            raise ErrorDeNegocio("Seleccione el escenario base y el alternativo.")
        if base.taller_id != alt.taller_id:
            raise ErrorDeNegocio("Los escenarios deben pertenecer al mismo taller.")
        ind_b = calc_de(base, self._reg.list_by_escenario(base_id))
        ind_a = calc_de(alt, self._reg.list_by_escenario(alternativo_id))
        comparable, problemas = calculos.verificar_comparable(ind_b, ind_a)
        filas = calculos.comparar(ind_b, ind_a)
        proceso, sb, sa = [], {}, {}
        try:
            ctx = self._ctx.cargar(base.taller_id)
            exigir_simulable(ctx)
            rb, ra = simular_completo(ctx, base), simular_completo(ctx, alt)
            sb, sa = rb.series, ra.series
            proceso = _filas_proceso(rb, ra)
        except ErrorDeNegocio:
            pass
        return ResultadoComparacion(base, alt, ind_b, ind_a, comparable, problemas, filas, proceso, sb, sa)


def _var(b, a):
    if b in (None, 0) or a is None:
        return None
    return (a - b) / b * 100.0


def _filas_proceso(rb: ResultadoSimulacion, ra: ResultadoSimulacion) -> list[dict]:
    kpis = [
        ("Lotes completados (%)", rb.ind.completados_pct, ra.ind.completados_pct),
        ("Cierre de la última entrega (min)", rb.ind.makespan_min, ra.ind.makespan_min),
        ("Lead time medio por lote (min)", rb.ind.lead_time_prom_min, ra.ind.lead_time_prom_min),
        ("Rendimiento (unidades/h)", rb.ind.throughput_u_h, ra.ind.throughput_u_h),
        ("Pedidos a tiempo (%)", rb.ind.pedidos_a_tiempo_pct, ra.ind.pedidos_a_tiempo_pct),
        ("Tardanza media de pedidos (min)", rb.ind.tardanza_prom_min, ra.ind.tardanza_prom_min),
        ("Espera por transporte (min)", rb.ind.espera_transporte_prom_min, ra.ind.espera_transporte_prom_min),
    ]
    return [{"indicador": k, "base": b, "alternativo": a, "variacion_pct": _var(b, a)} for k, b, a in kpis]


class ExportarReporte:
    def __init__(self, comparar: CompararEscenarios, exportador: ExportadorReportes):
        self._comparar = comparar
        self._exp = exportador

    def execute(self, base_id: int, alternativo_id: int, ruta: str, formato: str) -> None:
        r = self._comparar.execute(base_id, alternativo_id)
        if not r.comparable:
            raise ErrorDeNegocio("No se puede exportar: " + " ".join(r.problemas))
        filas = [{"Indicador": f["indicador"], r.base.nombre: f["base"],
                  r.alternativo.nombre: f["alternativo"], "Variación (%)": f["variacion_pct"]}
                 for f in r.filas + r.filas_proceso]
        if formato == "csv":
            self._exp.exportar_csv(ruta, filas)
        else:
            meta = [("Escenario base", r.base.nombre), ("Escenario alternativo", r.alternativo.nombre),
                    ("Fórmula", "V = ((Xalt - Xbase) / Xbase) * 100")]
            self._exp.exportar_xlsx(ruta, "Comparación de escenarios", meta, filas)
