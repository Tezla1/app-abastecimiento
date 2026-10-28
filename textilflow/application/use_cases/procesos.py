# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Prendas, rutas de proceso y pedidos del taller, con sus validaciones.

from ...domain.alertas import validar_rutas
from ...domain.entities import Pedido, RutaProceso, TipoPrenda
from ..errors import ErrorDeNegocio
from ..ports import (EstacionRepository, PedidoRepository, RutaProcesoRepository, TipoPrendaRepository)
from .talleres import exigir_valido


class GestionarProcesos:
    def __init__(self, tipos: TipoPrendaRepository, rutas: RutaProcesoRepository,
                 pedidos: PedidoRepository, estaciones: EstacionRepository):
        self._tipos, self._rutas, self._pedidos, self._est = tipos, rutas, pedidos, estaciones

    def listar_tipos(self) -> list[TipoPrenda]:
        return sorted(self._tipos.list_all(), key=lambda t: t.id or 0)

    def guardar_tipo(self, t: TipoPrenda) -> TipoPrenda:
        exigir_valido(t)
        t.nombre = t.nombre.strip()
        for otro in self._tipos.list_all():
            if otro.nombre.lower() == t.nombre.lower() and otro.id != t.id:
                raise ErrorDeNegocio(f"Ya existe la prenda «{t.nombre}».")
        return self._tipos.update(t) if t.id else self._tipos.add(t)

    def eliminar_tipo(self, tipo_id: int) -> None:
        if (any(r.tipo_prenda_id == tipo_id for r in self._rutas.list_all())
                or any(p.tipo_prenda_id == tipo_id for p in self._pedidos.list_all())):
            raise ErrorDeNegocio("La prenda tiene rutas o pedidos asociados: elimínelos primero.")
        self._tipos.delete(tipo_id)

    def listar_rutas(self, taller_id: int) -> list[RutaProceso]:
        return self._rutas.list_by_taller(taller_id)

    def guardar_ruta(self, r: RutaProceso) -> RutaProceso:
        exigir_valido(r)
        if self._tipos.get(r.tipo_prenda_id) is None:
            raise ErrorDeNegocio("Seleccione una prenda válida.")
        r.secuencia = ">".join(r.pasos())
        errores = validar_rutas([r], self._est.list_by_taller(r.taller_id))
        if errores:
            raise ErrorDeNegocio(" ".join(errores))
        return self._rutas.update(r) if r.id else self._rutas.add(r)

    def eliminar_ruta(self, ruta_id: int) -> None:
        self._rutas.delete(ruta_id)

    def listar_pedidos(self, taller_id: int) -> list[Pedido]:
        return self._pedidos.list_by_taller(taller_id)

    def guardar_pedido(self, p: Pedido) -> Pedido:
        exigir_valido(p)
        if self._tipos.get(p.tipo_prenda_id) is None:
            raise ErrorDeNegocio("Seleccione una prenda válida.")
        return self._pedidos.update(p) if p.id else self._pedidos.add(p)

    def eliminar_pedido(self, pedido_id: int) -> None:
        self._pedidos.delete(pedido_id)
