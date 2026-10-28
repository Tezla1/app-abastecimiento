# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Rutas más cortas sobre la red de pasillos, con filtro por ancho mínimo, conectividad y nodos críticos.

import heapq
from dataclasses import dataclass
from typing import Iterable, Optional

from .entities import Conexion


@dataclass(frozen=True)
class Tramo:
    origen: str
    destino: str
    distancia_m: float
    ancho_m: float


@dataclass(frozen=True)
class Ruta:
    nodos: tuple
    tramos: tuple

    @property
    def distancia_m(self) -> float:
        return sum(t.distancia_m for t in self.tramos)

    @property
    def ancho_min_m(self) -> Optional[float]:
        return min((t.ancho_m for t in self.tramos), default=None)


def _adyacencia(conexiones: Iterable[Conexion], ancho_min_m: float) -> dict:
    adj: dict[str, list[Tramo]] = {}
    for c in conexiones:
        if c.ancho_m < ancho_min_m:
            continue
        adj.setdefault(c.origen, []).append(Tramo(c.origen, c.destino, c.distancia_m, c.ancho_m))
        if c.bidireccional:
            adj.setdefault(c.destino, []).append(Tramo(c.destino, c.origen, c.distancia_m, c.ancho_m))
    return adj


def ruta_mas_corta(conexiones: Iterable[Conexion], origen: str, destino: str,
                   ancho_min_m: float = 0.0, excluir: frozenset = frozenset()) -> Optional[Ruta]:
    if origen == destino:
        return Ruta((origen,), ())
    adj = _adyacencia(conexiones, ancho_min_m)
    dist = {origen: 0.0}
    previo: dict[str, Tramo] = {}
    cola = [(0.0, origen)]
    while cola:
        d, nodo = heapq.heappop(cola)
        if nodo == destino:
            break
        if d > dist.get(nodo, float("inf")):
            continue
        for t in adj.get(nodo, []):
            if t.destino in excluir and t.destino != destino:
                continue
            nd = d + t.distancia_m
            if nd < dist.get(t.destino, float("inf")):
                dist[t.destino] = nd
                previo[t.destino] = t
                heapq.heappush(cola, (nd, t.destino))
    if destino not in previo:
        return None
    tramos = []
    nodo = destino
    while nodo != origen:
        t = previo[nodo]
        tramos.append(t)
        nodo = t.origen
    tramos.reverse()
    return Ruta(tuple([origen] + [t.destino for t in tramos]), tuple(tramos))


def red_conexa(codigos: Iterable[str], conexiones: Iterable[Conexion]) -> bool:
    codigos = list(codigos)
    if len(codigos) <= 1:
        return True
    vecinos: dict[str, set] = {c: set() for c in codigos}
    for c in conexiones:
        if c.origen in vecinos and c.destino in vecinos:
            vecinos[c.origen].add(c.destino)
            vecinos[c.destino].add(c.origen)
    visto = {codigos[0]}
    pila = [codigos[0]]
    while pila:
        for v in vecinos[pila.pop()]:
            if v not in visto:
                visto.add(v)
                pila.append(v)
    return len(visto) == len(codigos)


def _vecinos(codigos: Iterable[str], conexiones: Iterable[Conexion]) -> dict:
    v: dict[str, set] = {c: set() for c in codigos}
    for c in conexiones:
        if c.origen in v and c.destino in v:
            v[c.origen].add(c.destino)
            v[c.destino].add(c.origen)
    return v


def _componentes(vecinos: dict, ignorar_nodo: Optional[str] = None, ignorar_arco: Optional[frozenset] = None) -> int:
    visto: set = set()
    n = 0
    for ini in vecinos:
        if ini == ignorar_nodo or ini in visto:
            continue
        n += 1
        pila = [ini]
        visto.add(ini)
        while pila:
            a = pila.pop()
            for b in vecinos[a]:
                if b == ignorar_nodo or b in visto or (ignorar_arco and frozenset((a, b)) == ignorar_arco):
                    continue
                visto.add(b)
                pila.append(b)
    return n


def nodos_criticos(codigos: Iterable[str], conexiones: Iterable[Conexion]) -> dict:
    codigos, conexiones = list(codigos), list(conexiones)
    v = _vecinos(codigos, conexiones)
    base = _componentes(v)
    out = {}
    for n in codigos:
        partes = _componentes(v, ignorar_nodo=n)
        if partes > base:
            out[n] = partes
    return out


def arcos_criticos(codigos: Iterable[str], conexiones: Iterable[Conexion]) -> list:
    codigos, conexiones = list(codigos), list(conexiones)
    v = _vecinos(codigos, conexiones)
    base = _componentes(v)
    vistos, out = set(), []
    for c in conexiones:
        clave = frozenset((c.origen, c.destino))
        if clave in vistos or c.origen not in v or c.destino not in v:
            continue
        vistos.add(clave)
        if _componentes(v, ignorar_arco=clave) > base:
            out.append(c)
    return out
