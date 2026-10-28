import math
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .entities import (PREFIJO_GRUPO, Conexion, Estacion, Pedido, RutaProceso, TipoPrenda)
from .routing import arcos_criticos, nodos_criticos, ruta_mas_corta
from .simulacion import ResultadoProceso, generar_lotes


@dataclass
class EstadoEstacion:
    codigo: str
    nombre: str
    capacidad: int
    utilizacion_pct: float
    espera_prom_min: float
    espera_max_min: float
    cola_max: int
    lotes: int
    unidades: int
    carga_ofrecida_pct: Optional[float] = None


def analizar_estaciones(res: ResultadoProceso, estaciones: Iterable[Estacion],
                        carga_ofrecida: Optional[dict] = None) -> list[EstadoEstacion]:
    h = res.params.tiempo_observacion_min
    out = []
    for e in estaciones:
        if e.tiempo_proceso_min <= 0:
            continue
        vs = [v for v in res.visitas if v.estacion == e.codigo]
        iniciadas = [v for v in vs if v.inicio_min is not None]
        ocupado = sum(max(0.0, min(v.fin_min, h) - min(v.inicio_min, h)) for v in iniciadas)
        esperas = [v.inicio_min - v.llegada_min for v in iniciadas]
        eventos = []
        for v in vs:
            fin_espera = v.inicio_min if v.inicio_min is not None else float("inf")
            if fin_espera - v.llegada_min > 1e-9:
                eventos += [(v.llegada_min, 1), (fin_espera, -1)]
        cola = actual = 0
        for _, d in sorted(eventos, key=lambda x: (x[0], x[1])):
            actual += d
            cola = max(cola, actual)
        rho = None
        if carga_ofrecida and e.codigo in carga_ofrecida:
            rho = carga_ofrecida[e.codigo][1]
        out.append(EstadoEstacion(
            e.codigo, e.nombre, e.capacidad, ocupado / (e.capacidad * h) * 100 if h else 0.0,
            sum(esperas) / len(esperas) if esperas else 0.0, max(esperas, default=0.0), cola,
            len(iniciadas), sum(v.unidades for v in iniciadas), rho))
    return out


# miro la peor de las dos medidas, la simulada o la analítica
def carga_de(e: EstadoEstacion) -> float:
    return max(e.utilizacion_pct, e.carga_ofrecida_pct or 0.0)


def cuello_de_botella(estados: list[EstadoEstacion], umbral_pct: float = 85.0) -> Optional[EstadoEstacion]:
    if not estados:
        return None
    # si hay empate gana la que más hace esperar
    peor = max(estados, key=lambda s: (carga_de(s), s.espera_prom_min))
    return peor if carga_de(peor) >= umbral_pct else None


@dataclass
class IndicadoresProceso:
    lotes: int = 0
    lotes_completados: int = 0
    lotes_fallidos: int = 0
    unidades: int = 0
    unidades_completadas: int = 0
    completados_pct: float = 0.0
    makespan_min: float = 0.0
    lead_time_prom_min: Optional[float] = None
    lead_time_por_prioridad: dict = field(default_factory=dict)
    throughput_u_h: float = 0.0
    pedidos: int = 0
    pedidos_con_vencimiento: int = 0
    pedidos_a_tiempo_pct: Optional[float] = None
    tardanza_prom_min: Optional[float] = None
    pedidos_tarde: list = field(default_factory=list)
    espera_transporte_prom_min: Optional[float] = None


def indicadores_proceso(res: ResultadoProceso, pedidos: Iterable[Pedido]) -> IndicadoresProceso:
    ind = IndicadoresProceso()
    ind.lotes = len(res.lotes)
    ind.unidades = sum(l.unidades for l in res.lotes)
    hechos = [l for l in res.lotes if l.estado == "completado"]
    ind.lotes_completados = len(hechos)
    ind.lotes_fallidos = sum(1 for l in res.lotes if l.estado == "fallido")
    ind.unidades_completadas = sum(l.unidades for l in hechos)
    ind.completados_pct = ind.lotes_completados / ind.lotes * 100 if ind.lotes else 0.0
    if hechos:
        ind.makespan_min = max(l.fin_min for l in hechos)
        leads = [l.fin_min - l.llegada_min for l in hechos]
        ind.lead_time_prom_min = sum(leads) / len(leads)
        for pr in sorted({l.prioridad for l in hechos}):
            xs = [l.fin_min - l.llegada_min for l in hechos if l.prioridad == pr]
            ind.lead_time_por_prioridad[pr] = sum(xs) / len(xs)
        if ind.makespan_min > 0:
            ind.throughput_u_h = ind.unidades_completadas / (ind.makespan_min / 60.0)
    atendidas = [t for t in res.tareas if t.atendida]
    if atendidas:
        ind.espera_transporte_prom_min = sum(t.espera_min for t in atendidas) / len(atendidas)
    por_pedido: dict[int, list] = {}
    for l in res.lotes:
        por_pedido.setdefault(l.pedido_id, []).append(l)
    ind.pedidos = len(por_pedido) + len(res.pedidos_sin_ruta)
    tardanzas = []
    con_venc = 0
    a_tiempo = 0
    for p in pedidos:
        if not p.vencimiento_min or p.id not in por_pedido:
            continue
        con_venc += 1
        ls = por_pedido[p.id]
        if all(l.estado == "completado" for l in ls):
            fin = max(l.fin_min for l in ls)
            if fin <= p.vencimiento_min:
                a_tiempo += 1
            else:
                tardanzas.append(fin - p.vencimiento_min)
                ind.pedidos_tarde.append((p.id, p.prioridad, fin - p.vencimiento_min))
        else:
            ind.pedidos_tarde.append((p.id, p.prioridad, None))
    ind.pedidos_con_vencimiento = con_venc
    if con_venc:
        ind.pedidos_a_tiempo_pct = a_tiempo / con_venc * 100
    if tardanzas:
        ind.tardanza_prom_min = sum(tardanzas) / len(tardanzas)
    return ind


@dataclass
class Trafico:
    arcos: dict = field(default_factory=dict)
    arcos_kg: dict = field(default_factory=dict)
    nodos: dict = field(default_factory=dict)

    def max_arco(self) -> int:
        return max(self.arcos.values(), default=0)

    def max_nodo(self) -> int:
        return max(self.nodos.values(), default=0)


def trafico(res: ResultadoProceso) -> Trafico:
    t = Trafico()
    for m in res.movimientos:
        for n in m.ruta:
            t.nodos[n] = t.nodos.get(n, 0) + 1
        for a, b in zip(m.ruta, m.ruta[1:]):
            k = frozenset((a, b))
            t.arcos[k] = t.arcos.get(k, 0) + 1
            t.arcos_kg[k] = t.arcos_kg.get(k, 0.0) + m.kg
    return t


def series_tiempo(res: ResultadoProceso, estaciones: Iterable[Estacion], puntos: int = 160) -> dict:
    fin = max(res.t_fin_min, res.params.tiempo_observacion_min, 1.0)
    paso = fin / puntos
    ts = [i * paso for i in range(puntos + 1)]
    cola = {}
    for e in estaciones:
        if e.tiempo_proceso_min <= 0:
            continue
        vs = [v for v in res.visitas if v.estacion == e.codigo]
        cola[e.codigo] = [sum(1 for v in vs if v.llegada_min <= t and (v.inicio_min is None or v.inicio_min > t))
                          for t in ts]
    wip = [sum(1 for l in res.lotes if l.llegada_min <= t and (l.fin_min is None or l.fin_min > t)
               and l.estado != "fallido") for t in ts]
    hechos = [sum(1 for l in res.lotes if l.fin_min is not None and l.fin_min <= t) for t in ts]
    return {"t": ts, "wip": wip, "completados": hechos, "cola": cola}


def _miembros(estaciones: Iterable[Estacion], token: str) -> list[Estacion]:
    estaciones = list(estaciones)
    if token.startswith(PREFIJO_GRUPO):
        return [e for e in estaciones if e.grupo == token[1:]]
    return [e for e in estaciones if e.codigo == token]


def carga_ofrecida(estaciones: Iterable[Estacion], tipos: Iterable[TipoPrenda], rutas: Iterable[RutaProceso],
                   pedidos: Iterable[Pedido], horizonte_min: float, factor_demanda_pct: float = 100.0) -> dict:
    estaciones = list(estaciones)
    lotes, _ = generar_lotes(pedidos, tipos, rutas, factor_demanda_pct)
    carga = {e.codigo: 0.0 for e in estaciones if e.tiempo_proceso_min > 0}
    for l in lotes:
        for token in l.pasos[1:-1]:
            ms = [e for e in _miembros(estaciones, token) if e.tiempo_proceso_min > 0]
            for e in ms:
                carga[e.codigo] += l.unidades * e.tiempo_proceso_min * l.factor / len(ms)
    cap = {e.codigo: e.capacidad for e in estaciones}
    return {c: (m, m / (cap[c] * horizonte_min) * 100 if horizonte_min else 0.0) for c, m in carga.items()}


@dataclass
class RamaDistancia:
    prenda: str
    ruta: str
    fraccion_pct: float
    pasos: tuple
    distancia_m: float
    tiempo_transporte_min: float
    alcanzable: bool


def distancias_ramas(estaciones: Iterable[Estacion], conexiones: Iterable[Conexion], tipos: Iterable[TipoPrenda],
                     rutas: Iterable[RutaProceso], velocidad_ms: float, ancho_requerido_m: float = 0.0) -> list:
    estaciones, conexiones = list(estaciones), list(conexiones)
    tipos = {t.id: t for t in tipos}
    out = []
    for r in rutas:
        pos, total, ok, expandidos = None, 0.0, True, []
        for token in r.pasos():
            ms = _miembros(estaciones, token)
            if not ms:
                ok = False
                expandidos.append(token)
                continue
            if pos is None:
                elegido = ms[0].codigo
            else:
                cand = []
                for e in ms:
                    rt = ruta_mas_corta(conexiones, pos, e.codigo, ancho_requerido_m) if pos != e.codigo else None
                    cand.append((0.0 if pos == e.codigo else (rt.distancia_m if rt else float("inf")), e.codigo))
                d, elegido = min(cand)
                if math.isinf(d):
                    ok = False
                else:
                    total += d
            expandidos.append(elegido)
            pos = elegido
        t = tipos.get(r.tipo_prenda_id)
        out.append(RamaDistancia(t.nombre if t else "?", r.nombre, r.fraccion_pct, tuple(expandidos),
                                 total if ok else float("inf"),
                                 total / velocidad_ms / 60.0 if ok and velocidad_ms else float("inf"), ok))
    return out


def flota_analitica(res: ResultadoProceso, utilizacion_objetivo_pct: float) -> dict:
    ocupado = sum(t.recorrido_min for t in res.tareas if t.atendida)
    h = res.params.tiempo_observacion_min
    req = ocupado / (h * utilizacion_objetivo_pct / 100.0) if h and utilizacion_objetivo_pct else 0.0
    return {"trabajo_min": ocupado, "equipos": max(1, math.ceil(req - 1e-9)) if ocupado else 0,
            "equipos_exacto": req}


def resumen_recorridos(res: ResultadoProceso) -> dict:
    vacio = sum(m.distancia_m for m in res.movimientos if not m.cargado)
    cargado = sum(m.distancia_m for m in res.movimientos if m.cargado)
    viajes_cargados = sum(1 for m in res.movimientos if m.cargado)
    por_recurso: dict[int, dict] = {}
    for m in res.movimientos:
        r = por_recurso.setdefault(m.recurso, {"viajes": 0, "distancia_m": 0.0, "ocupado_min": 0.0})
        r["viajes"] += 1 if m.cargado else 0
        r["distancia_m"] += m.distancia_m
        r["ocupado_min"] += m.t1 - m.t0
    return {"viajes": viajes_cargados, "traslados": sum(1 for t in res.tareas if t.atendida),
            "distancia_cargada_m": cargado, "distancia_vacia_m": vacio,
            "distancia_total_m": cargado + vacio, "por_recurso": por_recurso}


@dataclass
class Critico:
    tipo: str
    elemento: str
    motivo: str
    severidad: str
    valor: Optional[float] = None


_ORDEN_SEV = {"CRÍTICA": 0, "ALTA": 1, "MEDIA": 2}


def componentes_criticos(estaciones: Iterable[Estacion], conexiones: Iterable[Conexion],
                         estados: Iterable[EstadoEstacion], traf: Optional[Trafico],
                         ancho_min_norma: float, umbral_cuello_pct: float) -> list[Critico]:
    estaciones, conexiones = list(estaciones), list(conexiones)
    nombres = {e.codigo: e.nombre or e.codigo for e in estaciones}
    codigos = [e.codigo for e in estaciones]
    out: list[Critico] = []
    for e in estados:
        carga = carga_de(e)
        if carga >= umbral_cuello_pct:
            sev = "CRÍTICA" if carga >= 100 else "ALTA"
            partes = [f"utilización simulada {e.utilizacion_pct:.0f} %"]
            if e.carga_ofrecida_pct is not None:
                partes.append(f"carga ofrecida (analítica) {e.carga_ofrecida_pct:.0f} %")
            partes.append(f"espera media {e.espera_prom_min:.1f} min, cola máx. {e.cola_max}")
            out.append(Critico("Cuello de botella", f"{e.codigo} · {e.nombre}", "; ".join(partes), sev, carga))
    for n, partes in nodos_criticos(codigos, conexiones).items():
        out.append(Critico("Nodo de red", f"{n} · {nombres[n]}",
                           f"Punto único de falla: si se bloquea, la red queda en {partes} partes.", "ALTA"))
    grado: dict[str, int] = {}
    for c in conexiones:
        grado[c.origen] = grado.get(c.origen, 0) + 1
        grado[c.destino] = grado.get(c.destino, 0) + 1
    for c in arcos_criticos(codigos, conexiones):
        terminal = min(grado.get(c.origen, 0), grado.get(c.destino, 0)) == 1
        out.append(Critico("Arco de red", f"{c.origen}–{c.destino} ({c.distancia_m:g} m)",
                           "Único acceso a un nodo terminal: sin ruta alternativa." if terminal
                           else "Único enlace entre dos zonas del taller: sin ruta alternativa.",
                           "MEDIA" if terminal else "ALTA"))
    for c in conexiones:
        if c.ancho_m < ancho_min_norma:
            out.append(Critico("Pasillo", f"{c.origen}–{c.destino}",
                               f"Ancho {c.ancho_m:g} m < mínimo normativo {ancho_min_norma:g} m (Res. 2400/1979 Art. 12).",
                               "ALTA", c.ancho_m))
    if traf and traf.arcos:
        k, v = max(traf.arcos.items(), key=lambda kv: kv[1])
        a, b = sorted(k)
        out.append(Critico("Arco más transitado", f"{a}–{b}", f"{v} pasadas de recursos en el turno.", "MEDIA", v))
    return sorted(out, key=lambda c: (_ORDEN_SEV[c.severidad], c.tipo))


def trafico_hasta(res: ResultadoProceso, t: float) -> Trafico:
    tr = Trafico()
    for m in res.movimientos:
        if m.t0 > t:
            continue
        for n in m.ruta:
            tr.nodos[n] = tr.nodos.get(n, 0) + 1
        for a, b in zip(m.ruta, m.ruta[1:]):
            k = frozenset((a, b))
            tr.arcos[k] = tr.arcos.get(k, 0) + 1
            tr.arcos_kg[k] = tr.arcos_kg.get(k, 0.0) + m.kg
    return tr


def caminos_por_lote(res: ResultadoProceso) -> dict:
    out: dict[int, list] = {}
    dist: dict[int, float] = {}
    for m in sorted(res.movimientos, key=lambda x: x.t0):
        if not m.cargado:
            continue
        seq = out.setdefault(m.lote, [])
        seq.extend(m.ruta[1:] if seq and seq[-1] == m.ruta[0] else m.ruta)
        dist[m.lote] = dist.get(m.lote, 0.0) + m.distancia_m
    return {k: (tuple(v), dist[k]) for k, v in out.items()}


def rutas_de_nodo(res: ResultadoProceso, nodo: str, pedido_id: Optional[int] = None) -> list[dict]:
    caminos = caminos_por_lote(res)
    grupos: dict[tuple, dict] = {}
    for l in res.lotes:
        if pedido_id is not None and l.pedido_id != pedido_id:
            continue
        info = caminos.get(l.id)
        if not info or nodo not in info[0]:
            continue
        seq, dist = info
        g = grupos.setdefault((l.pedido_id, l.ruta, seq), {
            "pedido_id": l.pedido_id, "prenda": l.prenda, "rama": l.ruta, "prioridad": l.prioridad,
            "camino": seq, "distancia_m": dist, "lotes": 0, "unidades": 0, "completados": 0, "principal": False})
        g["lotes"] += 1
        g["unidades"] += l.unidades
        g["completados"] += 1 if l.estado == "completado" else 0
    filas = sorted(grupos.values(), key=lambda g: (g["pedido_id"], -g["unidades"]))
    vistos = set()
    for g in filas:
        if g["pedido_id"] not in vistos:
            g["principal"] = True
            vistos.add(g["pedido_id"])
    return filas
