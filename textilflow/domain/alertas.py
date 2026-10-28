from dataclasses import dataclass
from typing import Iterable, Optional

from .analisis import EstadoEstacion, IndicadoresProceso, carga_de, cuello_de_botella
from .entities import (PREFIJO_GRUPO, Escenario, Estacion, Pedido, RutaProceso, TipoPrenda)
from .normativa import ADVERTENCIA, INCUMPLE, Cumplimiento
from .simulacion import ResultadoProceso

NIVELES = ("CRÍTICA", "ALTA", "MEDIA", "INFO")
_ORDEN = {n: i for i, n in enumerate(NIVELES)}


@dataclass
class Alerta:
    nivel: str
    codigo: str
    titulo: str
    detalle: str
    elemento: str = ""
    escenario: str = ""


def ordenar(alertas: Iterable[Alerta]) -> list[Alerta]:
    return sorted(alertas, key=lambda a: (_ORDEN[a.nivel], a.codigo, a.escenario))


def validar_rutas(rutas: Iterable[RutaProceso], estaciones: list[Estacion]) -> list[str]:
    por_codigo = {e.codigo: e for e in estaciones}
    grupos = {e.grupo for e in estaciones if e.grupo}
    errores = []
    for r in rutas:
        pasos = r.pasos()
        for p in pasos:
            if p.startswith(PREFIJO_GRUPO):
                if p[1:] not in grupos:
                    errores.append(f"Ruta «{r.nombre}»: el grupo «{p}» no existe.")
            elif p not in por_codigo:
                errores.append(f"Ruta «{r.nombre}»: la estación «{p}» no existe.")
        if pasos and not pasos[0].startswith(PREFIJO_GRUPO) and pasos[0] in por_codigo \
                and por_codigo[pasos[0]].funcion != "ALMACEN":
            errores.append(f"Ruta «{r.nombre}»: debe empezar en el Almacén (empieza en «{pasos[0]}»).")
        if pasos and not pasos[-1].startswith(PREFIJO_GRUPO) and pasos[-1] in por_codigo \
                and por_codigo[pasos[-1]].funcion != "DESPACHO":
            errores.append(f"Ruta «{r.nombre}»: debe terminar en el Despacho (termina en «{pasos[-1]}»).")
    return errores


def alertas_estaticas(estaciones: list[Estacion], tipos: list[TipoPrenda], rutas: list[RutaProceso],
                      pedidos: list[Pedido], cumplimientos: Iterable[Cumplimiento]) -> list[Alerta]:
    out: list[Alerta] = []
    funciones = [e.funcion for e in estaciones]
    if funciones.count("ALMACEN") != 1:
        out.append(Alerta("CRÍTICA", "CFG-ALM", "Almacén no definido",
                          "Debe existir exactamente un Almacén (punto inicial de todas las rutas)."))
    if funciones.count("DESPACHO") != 1:
        out.append(Alerta("CRÍTICA", "CFG-DES", "Despacho no definido",
                          "Debe existir exactamente un Despacho (punto final de todas las rutas)."))
    for msg in validar_rutas(rutas, estaciones):
        out.append(Alerta("ALTA", "CFG-RUTA", "Ruta de proceso inválida", msg))
    con_ruta = {r.tipo_prenda_id for r in rutas}
    nombres = {t.id: t.nombre for t in tipos}
    for tid in sorted({p.tipo_prenda_id for p in pedidos} - con_ruta):
        out.append(Alerta("ALTA", "CFG-SINRUTA", "Prenda sin ruta de proceso",
                          f"Los pedidos de «{nombres.get(tid, tid)}» no se pueden simular: defina su ruta.",
                          nombres.get(tid, "")))
    for t in tipos:
        total = sum(r.fraccion_pct for r in rutas if r.tipo_prenda_id == t.id)
        if total and abs(total - 100) > 0.01:
            out.append(Alerta("MEDIA", "CFG-FRAC", "Fracciones de ruta ≠ 100 %",
                              f"Las ramas de «{t.nombre}» suman {total:g} %; se normalizan al simular.", t.nombre))
    for c in cumplimientos:
        if c.estado == INCUMPLE:
            out.append(Alerta("ALTA", "NOR-" + c.clave, "Incumple normativa", f"{c.regla}. {c.detalle}"))
        elif c.estado == ADVERTENCIA:
            out.append(Alerta("MEDIA", "NOR-" + c.clave, "Advertencia de normativa / diseño", f"{c.regla}. {c.detalle}"))
    return out


def alertas_escenario(par: dict, esc: Escenario, res: ResultadoProceso, estados: list[EstadoEstacion],
                      ind: IndicadoresProceso, calc: dict, pedidos: list[Pedido],
                      prendas: dict) -> list[Alerta]:
    out: list[Alerta] = []
    n = esc.nombre

    def add(nivel, codigo, titulo, detalle, elemento=""):
        out.append(Alerta(nivel, codigo, titulo, detalle, elemento, n))

    cuello = cuello_de_botella(estados, par["umbral_cuello_botella_pct"])
    if cuello:
        ofrecida = f", carga ofrecida {cuello.carga_ofrecida_pct:.0f} %" if cuello.carga_ofrecida_pct is not None else ""
        add("CRÍTICA" if carga_de(cuello) >= 100 else "ALTA", "SIM-CUELLO",
            f"Cuello de botella en {cuello.nombre or cuello.codigo}",
            f"Utilización {cuello.utilizacion_pct:.0f} %{ofrecida}, espera media {cuello.espera_prom_min:.1f} min, "
            f"cola máxima {cuello.cola_max} lotes. Aumente puestos o reparta con un grupo alternativo.",
            cuello.codigo)
    for e in estados:
        if e.espera_prom_min > par["umbral_espera_cola_min"] and (not cuello or e.codigo != cuello.codigo):
            add("MEDIA", "SIM-COLA", f"Cola larga en {e.nombre or e.codigo}",
                f"Espera media {e.espera_prom_min:.1f} min (umbral {par['umbral_espera_cola_min']:g} min).", e.codigo)
    for pid, prio, tard in ind.pedidos_tarde:
        nombre = prendas.get(pid, "?")
        if tard is None:
            add("CRÍTICA" if prio <= 2 else "ALTA", "SIM-INCOMPLETO", f"Pedido #{pid} ({nombre}) sin terminar",
                f"No se completó antes del cierre y tiene fecha límite (prioridad {prio}).", f"#{pid}")
        else:
            add("CRÍTICA" if prio <= 2 else "ALTA", "SIM-TARDE", f"Pedido #{pid} ({nombre}) vence tarde",
                f"Termina {tard:.0f} min después de su fecha límite (prioridad {prio}).", f"#{pid}")
    fallidos = [l for l in res.lotes if l.estado == "fallido"]
    if fallidos:
        motivos = sorted({l.motivo for l in fallidos})
        add("ALTA", "SIM-FALLIDO", f"{len(fallidos)} lote(s) no se pudieron transportar", "; ".join(motivos))
    pend = [l for l in res.lotes if l.estado == "en curso"]
    if pend:
        u = sum(l.unidades for l in pend)
        add("ALTA", "SIM-WIP", f"{len(pend)} lote(s) ({u} u) sin terminar al cierre del turno",
            "Hay trabajo en proceso al cerrar: falta capacidad de transporte o de proceso.")
    sin_atender = [t for t in res.tareas if not t.atendida]
    if sin_atender:
        add("ALTA", "SIM-TRASLADO", f"{len(sin_atender)} traslado(s) sin atender",
            f"Solicitudes atendidas: {calc.get('solicitudes_atendidas_pct') or 0:.0f} %.")
    util = calc.get("utilizacion_pct")
    if util is not None:
        if util >= par["umbral_saturacion_flota_pct"]:
            add("ALTA", "SIM-FLOTA-SAT", "Flota de transporte saturada",
                f"Utilización {util:.0f} % con {esc.num_recursos} recurso(s): agregue equipos.")
        elif util < par["umbral_flota_ociosa_pct"]:
            add("INFO", "SIM-FLOTA-OCIOSA", "Flota sobredimensionada",
                f"Utilización {util:.0f} % con {esc.num_recursos} recurso(s): podría usar menos equipos.")
    return out
