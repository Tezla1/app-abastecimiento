import math
from dataclasses import dataclass
from typing import Iterable, Optional

from .analisis import EstadoEstacion, IndicadoresProceso, carga_de, cuello_de_botella
from .entities import (MOTIVOS_CIERRE, PREFIJO_GRUPO, Cierre, Escenario, Estacion, Pedido, RutaProceso, TipoPrenda)
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
    solucion: str = ""        # posible solución, con cifras concretas cuando se pueden calcular


# alertas que describen un cuello de botella, y el tipo de limitación que señalan
TIPO_CUELLO = {
    "PRE-CUELLO": "Proceso (previsto)",
    "SIM-CUELLO": "Proceso",
    "SIM-COLA": "Cola",
    "SIM-FLOTA-SAT": "Transporte",
    "SIM-ESPERA-TRANSP": "Transporte",
    "SIM-TRASLADO": "Transporte",
    "SIM-PASILLO": "Pasillo",
    "SIM-WIP": "Capacidad del turno",
}


def cuellos_de_botella(alertas: Iterable[Alerta]) -> list[Alerta]:
    """Alertas que son cuellos de botella, de la más grave a la menos grave."""
    return [a for a in ordenar(alertas) if a.codigo in TIPO_CUELLO]


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


_SOLUCION_NORMA = {
    "ancho_min_pasillo_m": "Ensanche los pasillos señalados o retire lo que los obstruye hasta cumplir el mínimo; si el "
                           "dato está mal, corrija el ancho en «Conexiones / Arcos».",
    "dist_min_entre_maquinas_m": "Separe las áreas indicadas cambiando su posición (X, Y) en «Estaciones / Nodos» hasta "
                                 "cumplir la distancia mínima entre equipos.",
    "holgura_lateral_robot_m": "Ensanche los pasillos vetados, use un robot más angosto (Diseño conceptual del robot) o "
                               "excluya esos tramos de las rutas del AMR.",
    "vel_max_zona_compartida_ms": "Baje la velocidad del escenario al límite, o separe el recorrido del AMR de las zonas "
                                  "con personas.",
    "carga_manual_max_hombres_kg": "Use carro o ayuda mecánica, o reduzca la capacidad por viaje del escenario manual.",
    "carga_manual_max_mujeres_kg": "Asigne el traslado con criterio, use carro o ayuda mecánica, o reduzca la "
                                   "capacidad por viaje.",
}


def _solucion_norma(clave: str, estado: str) -> str:
    if clave == "area_min_por_trabajador_m2":
        if estado == INCUMPLE:
            return "Amplíe el área disponible o reduzca el número de operadores por turno (por ejemplo, con dos turnos)."
        return "Registre el área y el número de operadores en «Caracterización del taller» para poder verificar la regla."
    return _SOLUCION_NORMA.get(clave, "Revise el dato señalado y ajústelo hasta cumplir la regla.")


def alertas_estaticas(estaciones: list[Estacion], tipos: list[TipoPrenda], rutas: list[RutaProceso],
                      pedidos: list[Pedido], cumplimientos: Iterable[Cumplimiento]) -> list[Alerta]:
    out: list[Alerta] = []
    funciones = [e.funcion for e in estaciones]
    if funciones.count("ALMACEN") != 1:
        out.append(Alerta("CRÍTICA", "CFG-ALM", "Almacén no definido",
                          "Debe existir exactamente un Almacén (punto inicial de todas las rutas).",
                          solucion="En «Layout y movimientos → Estaciones / Nodos» cree una estación con función "
                                   "«Almacén (punto inicial)»; si hay más de una, cambie la función de las sobrantes."))
    if funciones.count("DESPACHO") != 1:
        out.append(Alerta("CRÍTICA", "CFG-DES", "Despacho no definido",
                          "Debe existir exactamente un Despacho (punto final de todas las rutas).",
                          solucion="En «Layout y movimientos → Estaciones / Nodos» cree una estación con función "
                                   "«Despacho (punto final)»; si hay más de una, cambie la función de las sobrantes."))
    for msg in validar_rutas(rutas, estaciones):
        out.append(Alerta("ALTA", "CFG-RUTA", "Ruta de proceso inválida", msg,
                          solucion="Corrija la secuencia en «Layout y movimientos → Rutas de proceso»: use códigos de "
                                   "áreas que existan (o «@GRUPO» de un grupo existente), empiece en el Almacén y "
                                   "termine en el Despacho. Ej.: A>C>@COSTURA>I>E>D."))
    con_ruta = {r.tipo_prenda_id for r in rutas}
    nombres = {t.id: t.nombre for t in tipos}
    for tid in sorted({p.tipo_prenda_id for p in pedidos} - con_ruta):
        out.append(Alerta("ALTA", "CFG-SINRUTA", "Prenda sin ruta de proceso",
                          f"Los pedidos de «{nombres.get(tid, tid)}» no se pueden simular: defina su ruta.",
                          nombres.get(tid, ""),
                          solucion="Cree al menos una rama para esa prenda en «Layout y movimientos → Rutas de "
                                   "proceso» (Ej.: A>C>@COSTURA>I>E>D, 100 %), o borre los pedidos si ya no se fabrica."))
    for t in tipos:
        total = sum(r.fraccion_pct for r in rutas if r.tipo_prenda_id == t.id)
        if total and abs(total - 100) > 0.01:
            out.append(Alerta("MEDIA", "CFG-FRAC", "Fracciones de ruta ≠ 100 %",
                              f"Las ramas de «{t.nombre}» suman {total:g} %; se normalizan al simular.", t.nombre,
                              solucion="Ajuste los porcentajes en «Rutas de proceso» para que sumen 100 % "
                                       "(Ej.: 70 + 30), así el reparto es el que usted espera."))
    for c in cumplimientos:
        if c.estado == INCUMPLE:
            out.append(Alerta("ALTA", "NOR-" + c.clave, "Incumple normativa", f"{c.regla}. {c.detalle}",
                              solucion=_solucion_norma(c.clave, c.estado)))
        elif c.estado == ADVERTENCIA:
            out.append(Alerta("MEDIA", "NOR-" + c.clave, "Advertencia de normativa / diseño", f"{c.regla}. {c.detalle}",
                              solucion=_solucion_norma(c.clave, c.estado)))
    return out


def alertas_cierres(cierres: Iterable[Cierre], estaciones: list[Estacion]) -> list[Alerta]:
    nombres = {e.codigo: e.nombre or e.codigo for e in estaciones}
    out = []
    for c in cierres:
        if not c.vigente:
            continue
        ventana = "todo el turno" if not c.desde_min and not c.hasta_min else (
            f"desde el min {c.desde_min:g}" + (f" hasta el min {c.hasta_min:g}" if c.hasta_min else " sin reapertura"))
        paso = "también cierra el paso" if c.bloquea_paso else "el paso sigue abierto"
        out.append(Alerta("ALTA", "CIERRE", f"Área cerrada: {nombres.get(c.codigo, c.codigo)}",
                          f"{MOTIVOS_CIERRE.get(c.motivo, c.motivo)} · {ventana} · {paso}."
                          + (f" {c.detalle}" if c.detalle else ""), c.codigo,
                          solucion="Compare el escenario con y sin el cierre en «Contingencias y cierres» para medir el "
                                   "impacto. Para mitigarlo: reparta la carga con una estación gemela del mismo grupo "
                                   "(«@GRUPO»), cree una ruta alterna, programe el mantenimiento fuera de turno o "
                                   "adelante la reapertura. Si el cierre ya no aplica, desmarque «Cierre activo»."))
    return out


def _puestos_necesarios(capacidad: int, carga_pct: float, objetivo_pct: float) -> int:
    """Puestos en paralelo con los que la carga quedaría cerca de la utilización objetivo."""
    return max(capacidad + 1, math.ceil(capacidad * carga_pct / max(objetivo_pct, 1.0)))


def _solucion_estacion(est: Optional[Estacion], estaciones: list[Estacion], capacidad: int, carga_pct: float,
                       objetivo_pct: float) -> str:
    n = _puestos_necesarios(capacidad, carga_pct, objetivo_pct)
    partes = [f"Suba los puestos en paralelo de {capacidad} a {n} (la utilización quedaría cerca de {objetivo_pct:g} %)."]
    if est is not None and est.tiempo_proceso_min > 0:
        t2 = est.tiempo_proceso_min * objetivo_pct / carga_pct
        partes.append(f"O reduzca el tiempo de proceso de {est.tiempo_proceso_min:g} a ≈ {t2:.2f} min/unidad "
                      "(mejora de método, ayudas o máquina más rápida).")
    if est is not None:
        hermanas = [e for e in estaciones if est.grupo and e.grupo == est.grupo and e.codigo != est.codigo]
        if hermanas:
            partes.append(f"Reparta la carga con las otras estaciones del grupo «{est.grupo}» "
                          f"({', '.join(h.codigo for h in hermanas)}) usando «@{est.grupo}» en las rutas.")
        else:
            partes.append("O cree una estación gemela, póngales el mismo grupo y use «@GRUPO» en las rutas "
                          "para repartir los lotes.")
    if carga_pct >= 100:
        partes.append("La carga supera la capacidad: sin cambios la cola crece durante todo el turno.")
    return " ".join(partes)


def alertas_prediccion(par: dict, esc: Escenario, estaciones: list[Estacion], carga: dict) -> list[Alerta]:
    """Cuellos probables antes de simular, con la carga ofrecida (cálculo analítico)."""
    out = []
    por_codigo = {e.codigo: e for e in estaciones}
    for codigo, (_, pct) in sorted(carga.items(), key=lambda kv: -kv[1][1]):
        if pct < par["umbral_cuello_botella_pct"]:
            continue
        e = por_codigo[codigo]
        out.append(Alerta(
            "CRÍTICA" if pct >= 100 else "ALTA", "PRE-CUELLO",
            f"Posible cuello de botella en {e.nombre or e.codigo} (sin simular)",
            f"La carga ofrecida por los pedidos es {pct:.0f} % de la capacidad de la estación en "
            f"{esc.tiempo_observacion_min:g} min. Se calculó sin simular; ejecute el escenario para confirmarlo.",
            e.codigo, esc.nombre,
            _solucion_estacion(e, estaciones, e.capacidad, pct, par["utilizacion_objetivo_flota_pct"])))
    return out


def alertas_escenario(par: dict, esc: Escenario, res: ResultadoProceso, estados: list[EstadoEstacion],
                      ind: IndicadoresProceso, calc: dict, pedidos: list[Pedido],
                      prendas: dict, estaciones: Optional[list[Estacion]] = None, traf=None) -> list[Alerta]:
    out: list[Alerta] = []
    n = esc.nombre
    estaciones = estaciones or []
    por_codigo = {e.codigo: e for e in estaciones}
    objetivo = par["utilizacion_objetivo_flota_pct"]

    def add(nivel, codigo, titulo, detalle, elemento="", solucion=""):
        out.append(Alerta(nivel, codigo, titulo, detalle, elemento, n, solucion))

    umbral = par["umbral_cuello_botella_pct"]
    cuellos = sorted((e for e in estados if carga_de(e) >= umbral),
                     key=lambda e: (-carga_de(e), -e.espera_prom_min))
    for cuello in cuellos:
        carga = carga_de(cuello)
        ofrecida = f", carga ofrecida {cuello.carga_ofrecida_pct:.0f} %" if cuello.carga_ofrecida_pct is not None else ""
        add("CRÍTICA" if carga >= 100 else "ALTA", "SIM-CUELLO",
            f"Cuello de botella en {cuello.nombre or cuello.codigo}",
            f"Utilización {cuello.utilizacion_pct:.0f} %{ofrecida}, espera media {cuello.espera_prom_min:.1f} min, "
            f"cola máxima {cuello.cola_max} lotes.",
            cuello.codigo,
            _solucion_estacion(por_codigo.get(cuello.codigo), estaciones, cuello.capacidad, carga, objetivo))
    codigos_cuello = {c.codigo for c in cuellos}
    nombres_cuello = ", ".join(c.nombre or c.codigo for c in cuellos)
    for e in estados:
        if e.espera_prom_min > par["umbral_espera_cola_min"] and e.codigo not in codigos_cuello:
            add("MEDIA", "SIM-COLA", f"Cola larga en {e.nombre or e.codigo}",
                f"Espera media {e.espera_prom_min:.1f} min (umbral {par['umbral_espera_cola_min']:g} min).", e.codigo,
                "Escalone la llegada de pedidos al almacén, use lotes más pequeños o agregue un puesto "
                f"({e.capacidad} → {e.capacidad + 1}). Si esta estación sigue a un cuello de botella, la cola se "
                "origina aguas arriba: atienda primero esa estación.")
    for pid, prio, tard in ind.pedidos_tarde:
        nombre = prendas.get(pid, "?")
        alivio = f" o alivie el cuello de botella de su ruta ({nombres_cuello})" if nombres_cuello else ""
        sol = f"Suba su prioridad, adelante su llegada al almacén, flexibilice la fecha límite{alivio}."
        if tard is None:
            add("CRÍTICA" if prio <= 2 else "ALTA", "SIM-INCOMPLETO", f"Pedido #{pid} ({nombre}) sin terminar",
                f"No se completó antes del cierre y tiene fecha límite (prioridad {prio}).", f"#{pid}", sol)
        else:
            add("CRÍTICA" if prio <= 2 else "ALTA", "SIM-TARDE", f"Pedido #{pid} ({nombre}) vence tarde",
                f"Termina {tard:.0f} min después de su fecha límite (prioridad {prio}).", f"#{pid}", sol)
    fallidos = [l for l in res.lotes if l.estado == "fallido"]
    if fallidos:
        motivos = sorted({l.motivo for l in fallidos})
        add("ALTA", "SIM-FALLIDO", f"{len(fallidos)} lote(s) no se pudieron transportar", "; ".join(motivos),
            solucion="Revise que haya conexiones entre las áreas de la ruta, que su ancho sea mayor al del robot, "
                     "que no estén cerradas y que el peso del lote no supere la capacidad por viaje.")
    pend = [l for l in res.lotes if l.estado == "en curso"]
    if pend:
        u = sum(l.unidades for l in pend)
        add("ALTA", "SIM-WIP", f"{len(pend)} lote(s) ({u} u) sin terminar al cierre del turno",
            "Hay trabajo en proceso al cerrar: falta capacidad de transporte o de proceso.",
            solucion="Aumente la duración del turno, agregue recursos de transporte"
                     + (f" o amplíe los cuellos de botella ({nombres_cuello})" if nombres_cuello else "")
                     + ", o reduzca la demanda del escenario.")
    sin_atender = [t for t in res.tareas if not t.atendida]
    if sin_atender:
        add("ALTA", "SIM-TRASLADO", f"{len(sin_atender)} traslado(s) sin atender",
            f"Solicitudes atendidas: {calc.get('solicitudes_atendidas_pct') or 0:.0f} %.",
            solucion=f"Agregue recursos de transporte (hoy {esc.num_recursos}), active el reposicionamiento en vacío "
                     "o alargue el turno.")
    util = calc.get("utilizacion_pct")
    if util is not None:
        if util >= par["umbral_saturacion_flota_pct"]:
            req = max(esc.num_recursos + 1, math.ceil(esc.num_recursos * util / max(objetivo, 1.0)))
            add("ALTA", "SIM-FLOTA-SAT", "Flota de transporte saturada",
                f"Utilización {util:.0f} % con {esc.num_recursos} recurso(s).",
                solucion=f"Pase de {esc.num_recursos} a {req} recursos (utilización ≈ {objetivo:g} %), o suba la "
                         "velocidad/capacidad por viaje, o acorte las distancias del layout.")
        elif util < par["umbral_flota_ociosa_pct"]:
            req = max(1, math.ceil(esc.num_recursos * util / max(objetivo, 1.0)))
            add("INFO", "SIM-FLOTA-OCIOSA", "Flota sobredimensionada",
                f"Utilización {util:.0f} % con {esc.num_recursos} recurso(s): podría usar menos equipos.",
                solucion=(f"Bastarían {req} recurso(s) (utilización ≈ {objetivo:g} %)." if req < esc.num_recursos
                          else "Mantenga la flota o use los equipos sobrantes en otras tareas."))
    espera_t = ind.espera_transporte_prom_min
    if espera_t is not None and espera_t > par["umbral_espera_cola_min"]:
        add("MEDIA", "SIM-ESPERA-TRANSP", "Los lotes esperan mucho el transporte",
            f"Espera media por un recurso de transporte {espera_t:.1f} min (umbral {par['umbral_espera_cola_min']:g} min).",
            solucion="El cuello está en el transporte: agregue recursos, active el reposicionamiento en vacío, "
                     "use la política de prioridad o agrupe traslados en lotes más grandes.")
    if traf and len(traf.arcos) >= 4:
        valores = sorted(traf.arcos.values())
        mediana = valores[len(valores) // 2]
        k, v = max(traf.arcos.items(), key=lambda kv: kv[1])
        if v >= 10 and v >= 3 * max(mediana, 1):
            a, b = sorted(k)
            add("MEDIA", "SIM-PASILLO", f"Pasillo congestionado: {a}–{b}",
                f"{v} pasadas en el turno, {v / max(mediana, 1):.1f} veces la mediana de los demás pasillos ({mediana}).",
                f"{a}–{b}",
                "Cree una conexión alternativa entre esas zonas para repartir el tráfico, ensanche el pasillo "
                "o reubique las áreas que más se comunican para acortar el recorrido.")
    return out
