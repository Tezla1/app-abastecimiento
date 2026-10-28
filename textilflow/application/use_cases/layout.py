import math
from typing import Optional

from ...domain.entities import Conexion, Estacion
from ...domain.routing import Ruta, ruta_mas_corta
from ..errors import ErrorDeNegocio
from ..ports import ConexionRepository, EstacionRepository, RutaProcesoRepository
from .talleres import exigir_valido


class GestionarLayout:

    def __init__(self, estaciones: EstacionRepository, conexiones: ConexionRepository,
                 rutas: RutaProcesoRepository):
        self._est = estaciones
        self._con = conexiones
        self._rut = rutas

    def listar_estaciones(self, taller_id: int) -> list[Estacion]:
        return self._est.list_by_taller(taller_id)

    def guardar_estacion(self, e: Estacion) -> Estacion:
        exigir_valido(e)
        e.codigo = e.codigo.strip()
        for otra in self._est.list_by_taller(e.taller_id):
            if otra.codigo == e.codigo and otra.id != e.id:
                raise ErrorDeNegocio(f"Ya existe una estación con código «{e.codigo}».")
            if e.funcion in ("ALMACEN", "DESPACHO") and otra.funcion == e.funcion and otra.id != e.id:
                raise ErrorDeNegocio(f"Ya existe un {e.funcion.title()} («{otra.codigo}»): solo puede haber uno.")
        if e.id:
            anterior = self._est.get(e.id)
            if anterior and anterior.codigo != e.codigo and self._referencias(e.taller_id, anterior.codigo):
                raise ErrorDeNegocio(
                    f"No se puede cambiar el código «{anterior.codigo}»: lo usan conexiones o rutas.")
            return self._est.update(e)
        return self._est.add(e)

    def eliminar_estacion(self, estacion_id: int) -> None:
        e = self._est.get(estacion_id)
        if e is None:
            raise ErrorDeNegocio("La estación ya no existe.")
        if self._referencias(e.taller_id, e.codigo):
            raise ErrorDeNegocio(
                f"No se puede eliminar «{e.codigo}»: tiene conexiones o rutas asociadas.")
        self._est.delete(estacion_id)

    def _referencias(self, taller_id: int, codigo: str) -> bool:
        return (any(codigo in (c.origen, c.destino) for c in self._con.list_by_taller(taller_id))
                or any(codigo in r.pasos() for r in self._rut.list_by_taller(taller_id)))

    def _exigir_estaciones(self, taller_id: int, *codigos: str) -> dict:
        por_codigo = {e.codigo: e for e in self._est.list_by_taller(taller_id)}
        for c in codigos:
            if c not in por_codigo:
                raise ErrorDeNegocio(f"La estación «{c}» no existe en este taller.")
        return por_codigo

    def listar_conexiones(self, taller_id: int) -> list[Conexion]:
        return self._con.list_by_taller(taller_id)

    def guardar_conexion(self, c: Conexion) -> Conexion:
        exigir_valido(c)
        est = self._exigir_estaciones(c.taller_id, c.origen, c.destino)
        if c.distancia_m <= 0:
            a, b = est[c.origen], est[c.destino]
            c.distancia_m = round(math.hypot(a.x - b.x, a.y - b.y), 2)
            if c.distancia_m <= 0:
                raise ErrorDeNegocio("Las estaciones están en el mismo punto: indique la distancia.")
        return self._con.update(c) if c.id else self._con.add(c)

    def eliminar_conexion(self, conexion_id: int) -> None:
        self._con.delete(conexion_id)

    def calcular_ruta(self, taller_id: int, origen: str, destino: str,
                      ancho_min_m: float = 0.0) -> Optional[Ruta]:
        self._exigir_estaciones(taller_id, origen, destino)
        return ruta_mas_corta(self._con.list_by_taller(taller_id), origen, destino, ancho_min_m)
