# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Unidades en almacén por prenda, avisos de compra y su paso de pendiente a recibida, que suma lo recibido al inventario.

from datetime import datetime
from typing import Optional

from ...domain.alertas import balance_stock
from ...domain.entities import ESTADOS_COMPRA, SolicitudCompra, Stock
from ..errors import ErrorDeNegocio
from ..ports import PedidoRepository, SolicitudCompraRepository, StockRepository, TipoPrendaRepository
from .talleres import exigir_valido


class GestionarInventario:

    def __init__(self, stock: StockRepository, compras: SolicitudCompraRepository,
                 pedidos: PedidoRepository, tipos: TipoPrendaRepository, talleres=None):
        self._stock, self._compras, self._pedidos, self._tipos = stock, compras, pedidos, tipos
        self._talleres = talleres

    def listar_stock(self, taller_id: int) -> list[Stock]:
        return sorted(self._stock.list_by_taller(taller_id), key=lambda s: s.id or 0)

    def guardar_stock(self, s: Stock) -> Stock:
        exigir_valido(s)
        if self._tipos.get(s.tipo_prenda_id) is None:
            raise ErrorDeNegocio("Seleccione una prenda válida.")
        previo = next((x for x in self._stock.list_by_taller(s.taller_id)
                       if x.tipo_prenda_id == s.tipo_prenda_id and x.id != s.id), None)
        if previo is not None:
            previo.unidades, previo.stock_minimo = s.unidades, s.stock_minimo
            return self._stock.update(previo)
        return self._stock.update(s) if s.id else self._stock.add(s)

    def eliminar_stock(self, stock_id: int) -> None:
        self._stock.delete(stock_id)

    def balance(self, taller_id: int, s: Stock) -> dict:
        return balance_stock(s, self._pedidos.list_by_taller(taller_id), self._compras.list_by_taller(taller_id))

    def listar_compras(self, taller_id: int) -> list[SolicitudCompra]:
        return sorted(self._compras.list_by_taller(taller_id), key=lambda c: c.id or 0, reverse=True)

    def generar_aviso(self, taller_id: int, tipo_prenda_id: int) -> SolicitudCompra:
        s = next((x for x in self._stock.list_by_taller(taller_id) if x.tipo_prenda_id == tipo_prenda_id), None)
        if s is None:
            raise ErrorDeNegocio("Registre primero las unidades en almacén de esa prenda.")
        cantidad = self.balance(taller_id, s)["sugerida"]
        if cantidad <= 0:
            raise ErrorDeNegocio("No hace falta comprar: las unidades cubren los pedidos y el mínimo, "
                                 "o ya hay una compra en camino por esa cantidad.")
        return self.guardar_compra(SolicitudCompra(
            taller_id, tipo_prenda_id, cantidad, "PENDIENTE", "Aviso generado desde el inventario del taller."))

    def guardar_compra(self, c: SolicitudCompra) -> SolicitudCompra:
        exigir_valido(c)
        if self._tipos.get(c.tipo_prenda_id) is None:
            raise ErrorDeNegocio("Seleccione una prenda válida.")
        if c.id is None:
            c.registrado = datetime.now().strftime("%Y-%m-%d %H:%M")
            return self._compras.add(c)
        anterior = self._compras.get(c.id)
        if anterior is None:
            raise ErrorDeNegocio("La solicitud ya no existe.")
        if anterior.estado in ("RECIBIDA", "CANCELADA"):
            raise ErrorDeNegocio(f"La solicitud ya está {ESTADOS_COMPRA[anterior.estado].split(' ')[0].lower()}: "
                                 "no se puede modificar. Registre un aviso nuevo si hace falta más.")
        c.registrado = anterior.registrado
        if c.estado == "RECIBIDA":
            self._sumar_al_stock(c)
        return self._compras.update(c)

    def _sumar_al_stock(self, c: SolicitudCompra) -> None:
        s = next((x for x in self._stock.list_by_taller(c.taller_id) if x.tipo_prenda_id == c.tipo_prenda_id), None)
        if s is None:
            self._stock.add(Stock(c.taller_id, c.tipo_prenda_id, c.cantidad, 0))
        else:
            s.unidades += c.cantidad
            self._stock.update(s)

    def eliminar_compra(self, compra_id: int) -> None:
        self._compras.delete(compra_id)

    def aviso_para_compras(self, taller_id: int) -> str:
        nombres = {t.id: t.nombre for t in self._tipos.list_all()}
        taller = self._talleres.get(taller_id) if self._talleres is not None else None
        taller_nombre = taller.nombre if taller else ""
        pend = [c for c in self.listar_compras(taller_id) if c.estado == "PENDIENTE"]
        if not pend:
            raise ErrorDeNegocio("No hay avisos de compra pendientes.")
        lineas = [f"Solicitud de compra · {taller_nombre or 'Taller'} · {datetime.now():%Y-%m-%d %H:%M}",
                  "Se requiere hacer el pedido de reposición de las siguientes prendas:", ""]
        lineas += [f"- {nombres.get(c.tipo_prenda_id, '?')}: {c.cantidad} unidades" + (f" ({c.nota})" if c.nota else "")
                   for c in pend]
        lineas += ["", "Por favor confirmar cuando el pedido esté hecho y la fecha estimada de llegada."]
        return "\n".join(lineas)
