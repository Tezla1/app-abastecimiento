import heapq
import itertools
import math
import random
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .entities import (PREFIJO_GRUPO, Conexion, Estacion, Pedido, RutaProceso, TipoPrenda)
from .routing import Ruta, ruta_mas_corta


@dataclass(frozen=True)
class ParametrosSimulacion:
    num_recursos: int
    velocidad_ms: float
    capacidad_kg: float
    t_carga_s: float
    t_descarga_s: float
    nodo_inicial: str
    reposicionamiento: bool
    ancho_requerido_m: float
    tiempo_observacion_min: float
    politica: str = "PRIORIDAD"
    balanceo: bool = True
    factor_demanda_pct: float = 100.0
    variabilidad_pct: float = 0.0
    semilla: int = 1


@dataclass
class Lote:
    id: int
    pedido_id: int
    prenda: str
    ruta: str
    pasos: tuple
    unidades: int
    peso_unit_kg: float
    factor: float
    prioridad: int
    llegada_min: float
    vencimiento_min: float
    pos: str = ""
    paso: int = 0
    fin_min: Optional[float] = None
    estado: str = "en curso"
    motivo: str = ""
    compromiso: Optional[tuple] = None


@dataclass
class Visita:
    estacion: str
    lote: int
    pedido_id: int
    unidades: int
    prioridad: int
    llegada_min: float
    inicio_min: Optional[float] = None
    fin_min: Optional[float] = None


@dataclass
class Movimiento:
    recurso: int
    t0: float
    t1: float
    ruta: tuple
    cargado: bool
    lote: int
    pedido_id: int
    kg: float
    distancia_m: float


@dataclass
class Tarea:
    pedido_id: int
    lote: int
    desde: str
    hacia: str
    atendida: bool
    espera_min: float = 0.0
    recorrido_min: float = 0.0
    distancia_m: float = 0.0
    inicio_min: float = 0.0
    fin_min: float = 0.0
    recurso: int = 0
    viajes: int = 0
    detalle: str = ""


@dataclass
class ResultadoProceso:
    params: ParametrosSimulacion
    lotes: list = field(default_factory=list)
    visitas: list = field(default_factory=list)
    movimientos: list = field(default_factory=list)
    tareas: list = field(default_factory=list)
    pedidos_sin_ruta: list = field(default_factory=list)
    t_fin_min: float = 0.0


def _repartir(total: int, pesos: list[float]) -> list[int]:
    suma = sum(pesos)
    cuotas = [total * p / suma for p in pesos]
    base = [int(c) for c in cuotas]
    for i in sorted(range(len(pesos)), key=lambda i: (-(cuotas[i] - base[i]), i))[: total - sum(base)]:
        base[i] += 1
    return base


def generar_lotes(pedidos: Iterable[Pedido], tipos: Iterable[TipoPrenda], rutas: Iterable[RutaProceso],
                  factor_demanda_pct: float = 100.0) -> tuple[list[Lote], list[int]]:
    tipos = {t.id: t for t in tipos}
    por_tipo: dict[int, list[RutaProceso]] = {}
    for r in sorted(rutas, key=lambda r: r.id or 0):
        por_tipo.setdefault(r.tipo_prenda_id, []).append(r)
    lotes: list[Lote] = []
    sin_ruta: list[int] = []
    for p in sorted(pedidos, key=lambda p: (p.llegada_min, p.id or 0)):
        tipo, ramas = tipos.get(p.tipo_prenda_id), por_tipo.get(p.tipo_prenda_id, [])
        total = round(p.cantidad * factor_demanda_pct / 100.0)
        if tipo is None or not ramas or total < 1:
            if total >= 1:
                sin_ruta.append(p.id)
            continue
        for rama, unidades in zip(ramas, _repartir(total, [r.fraccion_pct for r in ramas])):
            if unidades < 1:
                continue
            n = math.ceil(unidades / tipo.unidades_por_lote)
            for k in range(n):
                u = unidades // n + (1 if k < unidades % n else 0)
                lotes.append(Lote(len(lotes) + 1, p.id, tipo.nombre, rama.nombre, tuple(rama.pasos()), u,
                                  tipo.peso_unidad_kg, tipo.factor_proceso, p.prioridad, p.llegada_min,
                                  p.vencimiento_min))
    return lotes, sin_ruta


@dataclass
class _Recurso:
    idx: int
    pos: str
    libre: bool = True


@dataclass
class _Tarea:
    id: int
    lote: Lote
    desde: str
    hacia: str
    listo: float


@dataclass
class _Item:
    lote: Lote
    visita: Visita
    dur: float


@dataclass
class _Estado:
    libres: int
    cola: list = field(default_factory=list)
    comprometido_min: float = 0.0


class _Motor:
    def __init__(self, p: ParametrosSimulacion, estaciones: list[Estacion], conexiones: list[Conexion],
                 lotes: list[Lote]):
        self.p = p
        self.est = {e.codigo: e for e in estaciones}
        self.con = conexiones
        self.lotes = lotes
        self.grupos: dict[str, list[str]] = {}
        for e in sorted(estaciones, key=lambda e: e.codigo):
            if e.grupo:
                self.grupos.setdefault(e.grupo, []).append(e.codigo)
        self.estado = {e.codigo: _Estado(e.capacidad) for e in estaciones}
        self.rec = [_Recurso(i + 1, p.nodo_inicial) for i in range(p.num_recursos)]
        self.pendientes: list[_Tarea] = []
        self.heap: list = []
        # desempata los eventos que caen en el mismo minuto
        self.seq = itertools.count()
        self.ids = itertools.count(1)
        self.rr: dict[str, int] = {}
        self.rng = random.Random(p.semilla)
        self.cache: dict = {}
        self.res = ResultadoProceso(p)

    def ruta(self, a: str, b: str) -> Optional[Ruta]:
        # las mismas rutas se piden muchas veces, mejor guardarlas
        if (a, b) not in self.cache:
            self.cache[(a, b)] = ruta_mas_corta(self.con, a, b, self.p.ancho_requerido_m)
        return self.cache[(a, b)]

    def push(self, t: float, tipo: str, *datos) -> None:
        heapq.heappush(self.heap, (t, next(self.seq), tipo, datos))

    def clave(self, prioridad: int, listo: float, id_: int) -> tuple:
        return (prioridad, listo, id_) if self.p.politica == "PRIORIDAD" else (listo, id_)

    def duracion(self, lote: Lote, e: Estacion, con_ruido: bool) -> float:
        d = lote.unidades * e.tiempo_proceso_min * lote.factor
        v = self.p.variabilidad_pct / 100.0
        return d * self.rng.uniform(1 - v, 1 + v) if con_ruido and v > 0 else d

    def correr(self) -> ResultadoProceso:
        for lote in self.lotes:
            self.push(lote.llegada_min, "llega", lote)
        while self.heap:
            t, _, tipo, datos = heapq.heappop(self.heap)
            self.res.t_fin_min = max(self.res.t_fin_min, t)
            if tipo == "llega":
                lote = datos[0]
                self.iniciar_lote(lote, t)
            elif tipo == "fin_tarea":
                rec, tarea = datos
                rec.libre = True
                rec.pos = tarea.hacia
                self.llegada(tarea.lote, tarea.hacia, t)
            elif tipo == "fin_proceso":
                code, lote = datos
                st = self.estado[code]
                st.libres += 1
                st.comprometido_min = max(0.0, st.comprometido_min - lote.compromiso[1]) if lote.compromiso else st.comprometido_min
                lote.compromiso = None
                self.solicitar_siguiente(lote, t)
                self.iniciar_procesos(code, t)
            self.despachar(t)
        self.cerrar()
        self.res.lotes = self.lotes
        return self.res

    def iniciar_lote(self, lote: Lote, t: float) -> None:
        primero = self.resolver(lote.pasos[0], lote, t, es_inicio=True)
        if primero is None:
            self.fallar_lote(lote, "El primer paso de la ruta no existe en el taller.")
            return
        lote.pos, lote.paso = primero, 0
        self.solicitar_siguiente(lote, t)

    def resolver(self, token: str, lote: Lote, t: float, es_inicio: bool = False) -> Optional[str]:
        if not token.startswith(PREFIJO_GRUPO):
            return token if token in self.est else None
        miembros = self.grupos.get(token[1:], [])
        if not miembros:
            return None
        if len(miembros) == 1:
            return miembros[0]
        # sin balanceo (o al arrancar) se reparte por turnos
        if not self.p.balanceo or es_inicio:
            i = self.rr.get(token, 0)
            self.rr[token] = i + 1
            return miembros[i % len(miembros)]
        v = self.p.velocidad_ms

        def estimado(code: str) -> tuple:
            r = self.ruta(lote.pos, code) if lote.pos != code else Ruta((code,), ())
            if r is None:
                return (float("inf"), code)
            espera = self.estado[code].comprometido_min / self.est[code].capacidad
            return (r.distancia_m / v / 60.0 + espera, code)

        # gana el que llegue antes contando la espera que ya tiene encima
        return min(miembros, key=estimado)

    def solicitar_siguiente(self, lote: Lote, t: float) -> None:
        if lote.paso >= len(lote.pasos) - 1:
            self.completar(lote, t)
            return
        destino = self.resolver(lote.pasos[lote.paso + 1], lote, t)
        if destino is None:
            self.fallar_lote(lote, f"El paso «{lote.pasos[lote.paso + 1]}» no existe o su grupo está vacío.")
            return
        e = self.est[destino]
        if e.tiempo_proceso_min > 0 and lote.paso + 1 < len(lote.pasos) - 1:
            mins = self.duracion(lote, e, con_ruido=False)
            self.estado[destino].comprometido_min += mins
            lote.compromiso = (destino, mins)
        if destino == lote.pos:
            self.llegada(lote, destino, t)
            return
        self.pendientes.append(_Tarea(next(self.ids), lote, lote.pos, destino, t))

    def llegada(self, lote: Lote, code: str, t: float) -> None:
        lote.pos = code
        lote.paso += 1
        if lote.paso >= len(lote.pasos) - 1:
            self.completar(lote, t)
            return
        e = self.est[code]
        if e.tiempo_proceso_min > 0:
            v = Visita(code, lote.id, lote.pedido_id, lote.unidades, lote.prioridad, t)
            self.res.visitas.append(v)
            self.estado[code].cola.append(_Item(lote, v, self.duracion(lote, e, con_ruido=True)))
            self.iniciar_procesos(code, t)
        else:
            self.solicitar_siguiente(lote, t)

    def completar(self, lote: Lote, t: float) -> None:
        lote.fin_min, lote.estado = t, "completado"

    def fallar_lote(self, lote: Lote, motivo: str) -> None:
        lote.estado, lote.motivo = "fallido", motivo
        if lote.compromiso:
            st = self.estado[lote.compromiso[0]]
            st.comprometido_min = max(0.0, st.comprometido_min - lote.compromiso[1])
            lote.compromiso = None

    def iniciar_procesos(self, code: str, t: float) -> None:
        st = self.estado[code]
        while st.libres > 0 and st.cola and t < self.p.tiempo_observacion_min:
            st.cola.sort(key=lambda i: self.clave(i.lote.prioridad, i.visita.llegada_min, i.lote.id))
            item = st.cola.pop(0)
            st.libres -= 1
            item.visita.inicio_min, item.visita.fin_min = t, t + item.dur
            self.push(t + item.dur, "fin_proceso", code, item.lote)

    def despachar(self, t: float) -> None:
        if t >= self.p.tiempo_observacion_min:
            return
        while self.pendientes and any(r.libre for r in self.rec):
            # son pocas tareas, ordenar cada vez no pesa
            self.pendientes.sort(key=lambda x: self.clave(x.lote.prioridad, x.listo, x.id))
            tarea = self.pendientes[0]
            lote = tarea.lote
            cargada = self.ruta(tarea.desde, tarea.hacia)
            if cargada is None:
                self.pendientes.pop(0)
                self.fallar_tarea(tarea, "Sin ruta factible (conectividad o ancho de pasillo).")
                continue
            if lote.peso_unit_kg > self.p.capacidad_kg:
                self.pendientes.pop(0)
                self.fallar_tarea(tarea, f"Una unidad ({lote.peso_unit_kg:g} kg) excede la capacidad "
                                         f"({self.p.capacidad_kg:g} kg).")
                continue
            libres = [r for r in self.rec if r.libre]
            if self.p.reposicionamiento:
                cand = []
                for r in libres:
                    vacia = self.ruta(r.pos, tarea.desde) if r.pos != tarea.desde else Ruta((r.pos,), ())
                    if vacia is not None:
                        cand.append((vacia.distancia_m, r.idx, r))
                if not cand:
                    alcanzable = any(r.pos == tarea.desde or self.ruta(r.pos, tarea.desde) for r in self.rec)
                    if alcanzable:
                        return
                    self.pendientes.pop(0)
                    self.fallar_tarea(tarea, "Sin ruta de reposicionamiento vacío.")
                    continue
                rec = min(cand, key=lambda c: c[:2])[2]
            else:
                rec = min(libres, key=lambda r: r.idx)
            self.pendientes.pop(0)
            self.ejecutar(tarea, rec, cargada, t)

    def fallar_tarea(self, tarea: _Tarea, motivo: str) -> None:
        self.res.tareas.append(Tarea(tarea.lote.pedido_id, tarea.lote.id, tarea.desde, tarea.hacia, False,
                                     detalle=motivo))
        self.fallar_lote(tarea.lote, motivo)

    def ejecutar(self, tarea: _Tarea, rec: _Recurso, cargada: Ruta, t: float) -> None:
        p, lote = self.p, tarea.lote
        # cuántas unidades caben en un viaje según el peso
        por_viaje = max(1, int(p.capacidad_kg // lote.peso_unit_kg))
        viajes = math.ceil(lote.unidades / por_viaje)
        restante, cursor, pos, dist_total = lote.unidades, t, rec.pos, 0.0
        for _ in range(viajes):
            if p.reposicionamiento and pos != tarea.desde:
                vacia = self.ruta(pos, tarea.desde)
                dur = vacia.distancia_m / p.velocidad_ms / 60.0
                self.res.movimientos.append(Movimiento(rec.idx, cursor, cursor + dur, vacia.nodos, False,
                                                       lote.id, lote.pedido_id, 0.0, vacia.distancia_m))
                cursor += dur
                dist_total += vacia.distancia_m
            cursor += p.t_carga_s / 60.0
            u = min(por_viaje, restante)
            restante -= u
            dur = cargada.distancia_m / p.velocidad_ms / 60.0
            self.res.movimientos.append(Movimiento(rec.idx, cursor, cursor + dur, cargada.nodos, True,
                                                   lote.id, lote.pedido_id, u * lote.peso_unit_kg,
                                                   cargada.distancia_m))
            cursor += dur
            dist_total += cargada.distancia_m
            cursor += p.t_descarga_s / 60.0
            pos = tarea.hacia
        rec.libre, rec.pos = False, tarea.hacia
        self.res.tareas.append(Tarea(
            lote.pedido_id, lote.id, tarea.desde, tarea.hacia, True, t - tarea.listo, cursor - t, dist_total,
            t, cursor, rec.idx, viajes,
            f"{viajes} viaje(s); {lote.unidades} u · {lote.unidades * lote.peso_unit_kg:.1f} kg."))
        self.push(cursor, "fin_tarea", rec, tarea)

    def cerrar(self) -> None:
        for tarea in self.pendientes:
            self.res.tareas.append(Tarea(tarea.lote.pedido_id, tarea.lote.id, tarea.desde, tarea.hacia, False,
                                         detalle="No se inició antes del cierre del turno."))
            if tarea.lote.estado == "en curso":
                tarea.lote.motivo = "Traslado sin atender al cierre del turno."
        for st in self.estado.values():
            for item in st.cola:
                if item.lote.estado == "en curso":
                    item.lote.motivo = "En cola de proceso al cierre del turno."
        for lote in self.lotes:
            if lote.estado == "en curso" and not lote.motivo:
                lote.motivo = "En proceso al cierre del turno."


def simular(p: ParametrosSimulacion, estaciones: Iterable[Estacion], conexiones: Iterable[Conexion],
            tipos: Iterable[TipoPrenda], rutas: Iterable[RutaProceso],
            pedidos: Iterable[Pedido]) -> ResultadoProceso:
    lotes, sin_ruta = generar_lotes(pedidos, tipos, rutas, p.factor_demanda_pct)
    motor = _Motor(p, list(estaciones), list(conexiones), lotes)
    res = motor.correr()
    res.pedidos_sin_ruta = sin_ruta
    return res
