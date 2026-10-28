# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Controlador de Layout y movimientos: estaciones, conexiones, prendas, rutas, pedidos, inventario y compras.

from PyQt6.QtWidgets import QApplication

from ...domain.entities import (ESTADOS_COMPRA, FUNCIONES, Conexion, Estacion, Pedido, RutaProceso, SolicitudCompra,
                                Stock, TipoPrenda)
from ..theme import COLOR_NIVEL, fmt
from .base import Controlador, construir_red, etiqueta_estacion


class LayoutController(Controlador):
    def __init__(self, vista, ctx, layout, procesos, inventario):
        super().__init__(vista, ctx)
        self._layout = layout
        self._procesos = procesos
        self._inv = inventario
        self._resaltar = frozenset()
        e, c = vista.estaciones, vista.conexiones
        pr, ru, pe = vista.prendas, vista.rutas, vista.pedidos
        pr.seleccionado.connect(self._cargar_prenda)
        pr.guardar_solicitado.connect(self._guardar_prenda)
        pr.eliminar_solicitado.connect(lambda i: self._eliminar(self._procesos.eliminar_tipo, i, pr, "Prenda eliminada."))
        ru.seleccionado.connect(self._cargar_ruta)
        ru.guardar_solicitado.connect(self._guardar_ruta)
        ru.eliminar_solicitado.connect(lambda i: self._eliminar(self._procesos.eliminar_ruta, i, ru, "Ruta eliminada."))
        pe.seleccionado.connect(self._cargar_pedido)
        pe.guardar_solicitado.connect(self._guardar_pedido)
        pe.eliminar_solicitado.connect(lambda i: self._eliminar(self._procesos.eliminar_pedido, i, pe, "Pedido eliminado."))
        iv, co = vista.inventario, vista.compras
        iv.seleccionado.connect(self._cargar_stock)
        iv.guardar_solicitado.connect(self._guardar_stock)
        iv.eliminar_solicitado.connect(lambda i: self._eliminar(self._inv.eliminar_stock, i, iv, "Registro de inventario eliminado."))
        co.seleccionado.connect(self._cargar_compra)
        co.guardar_solicitado.connect(self._guardar_compra)
        co.eliminar_solicitado.connect(lambda i: self._eliminar(self._inv.eliminar_compra, i, co, "Solicitud eliminada."))
        vista.aviso_solicitado.connect(self._generar_aviso)
        vista.copiar_aviso_solicitado.connect(self._copiar_aviso)
        e.seleccionado.connect(self._cargar_estacion)
        e.guardar_solicitado.connect(self._guardar_estacion)
        e.eliminar_solicitado.connect(lambda i: self._eliminar(self._layout.eliminar_estacion, i, e, "Estación eliminada."))
        c.seleccionado.connect(self._cargar_conexion)
        c.guardar_solicitado.connect(self._guardar_conexion)
        c.eliminar_solicitado.connect(lambda i: self._eliminar(self._layout.eliminar_conexion, i, c, "Conexión eliminada."))
        vista.ruta_solicitada.connect(self._calcular_ruta)
        vista.limpiar_ruta_solicitado.connect(self._limpiar_ruta)

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        est = self._layout.listar_estaciones(tid) if tid else []
        con = self._layout.listar_conexiones(tid) if tid else []
        tipos = self._procesos.listar_tipos()
        rutas = self._procesos.listar_rutas(tid) if tid else []
        peds = self._procesos.listar_pedidos(tid) if tid else []
        nombres = {t.id: t.nombre for t in tipos}
        self.vista.set_codigos([(e.codigo, etiqueta_estacion(e)) for e in est])
        self.vista.estaciones.set_filas(
            [[e.id, e.codigo, e.nombre, FUNCIONES[e.funcion], fmt(e.x), fmt(e.y),
              fmt(e.tiempo_proceso_min) if e.funcion == "PROCESO" else "—",
              e.capacidad if e.funcion == "PROCESO" else "—", e.grupo or "—"] for e in est], [e.id for e in est])
        self.vista.set_prendas([(t.id, t.nombre) for t in tipos])
        self.vista.set_ayuda_rutas(
            "Pasos separados por «>». Use códigos de área ("
            + ", ".join(e.codigo for e in est) + ") o «@GRUPO» para elegir la menos cargada de un grupo ("
            + (", ".join(sorted({"@" + e.grupo for e in est if e.grupo})) or "ninguno definido") + "). "
            "Debe empezar en el Almacén y terminar en el Despacho.")
        self.vista.prendas.set_filas([[t.id, t.nombre, fmt(t.peso_unidad_kg, 3), t.unidades_por_lote,
                                       fmt(t.factor_proceso)] for t in tipos], [t.id for t in tipos])
        self.vista.rutas.set_filas([[r.id, nombres.get(r.tipo_prenda_id, "?"), r.nombre, fmt(r.fraccion_pct, 1), r.secuencia]
                                    for r in rutas], [r.id for r in rutas])
        self.vista.pedidos.set_filas([[p.id, nombres.get(p.tipo_prenda_id, "?"), p.cantidad, p.prioridad,
                                       fmt(p.llegada_min, 0), fmt(p.vencimiento_min, 0) if p.vencimiento_min else "—",
                                       p.origen_datos] for p in peds], [p.id for p in peds])
        self._mostrar_inventario(tid, nombres)
        self.vista.conexiones.set_filas(
            [[c.id, c.origen, c.destino, fmt(c.distancia_m), fmt(c.ancho_m), "↔" if c.bidireccional else "→"]
             for c in con], [c.id for c in con])
        self.vista.dibujar_red(*construir_red(self._layout, tid, self._resaltar, self.ctx.cerrados()))

    def _mostrar_inventario(self, tid, nombres: dict) -> None:
        stocks = self._inv.listar_stock(tid) if tid else []
        filas, colores = [], []
        for s in stocks:
            b = self._inv.balance(tid, s)
            if s.unidades <= 0:
                estado, nivel = "Agotado", "CRÍTICA"
            elif b["falta"] > 0:
                estado, nivel = f"No alcanza (faltan {b['falta']})", "ALTA"
            elif s.unidades <= s.stock_minimo:
                estado, nivel = "Stock bajo", "MEDIA"
            else:
                estado, nivel = "Suficiente", None
            filas.append([s.id, nombres.get(s.tipo_prenda_id, "?"), s.unidades, s.stock_minimo, b["demanda"],
                          b["en_compra"], b["falta"], estado])
            colores.append(COLOR_NIVEL.get(nivel) if nivel else None)
        self.vista.inventario.set_filas(filas, [s.id for s in stocks], colores)
        compras = self._inv.listar_compras(tid) if tid else []
        self.vista.compras.set_filas(
            [[c.id, c.registrado or "—", nombres.get(c.tipo_prenda_id, "?"), c.cantidad,
              ESTADOS_COMPRA[c.estado].split(" ·")[0], c.nota or "—"] for c in compras], [c.id for c in compras])

    def _cargar_stock(self, id_: int) -> None:
        s = next((x for x in self._inv.listar_stock(self.ctx.taller_id) if x.id == id_), None)
        if s:
            self.vista.inventario.set_valores(vars(s), s.id)

    def _guardar_stock(self, d: dict) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        g = self._intentar(self._inv.guardar_stock, Stock(tid, d["tipo_prenda_id"] or 0, d["unidades"], d["stock_minimo"], d["id"]))
        if g:
            self.vista.inventario.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.inventario, "Inventario guardado.")

    def _cargar_compra(self, id_: int) -> None:
        c = next((x for x in self._inv.listar_compras(self.ctx.taller_id) if x.id == id_), None)
        if c:
            self.vista.compras.set_valores(vars(c), c.id)

    def _guardar_compra(self, d: dict) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        c = SolicitudCompra(tid, d["tipo_prenda_id"] or 0, d["cantidad"], d["estado"] or "PENDIENTE", d["nota"], "", d["id"])
        g = self._intentar(self._inv.guardar_compra, c)
        if g:
            self.vista.compras.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.compras, "Solicitud de compra guardada."
                              + (" Las unidades se sumaron al inventario." if g.estado == "RECIBIDA" else ""))

    def _generar_aviso(self, tipo_id: int) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        g = self._intentar(self._inv.generar_aviso, tid, tipo_id)
        if g:
            self.vista.compras.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.compras, f"Aviso de compra creado por {g.cantidad} unidades "
                              "(pestaña «Compras»). Copie el aviso y entréguelo a Compras.")

    def _copiar_aviso(self) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        texto = self._intentar(self._inv.aviso_para_compras, tid)
        if texto:
            QApplication.clipboard().setText(texto)
            self.vista.info("Aviso copiado al portapapeles. Péguelo en un correo o mensaje para Compras.")

    def _tras_cambio(self, panel, mensaje: str) -> None:
        self.refrescar()
        self.ctx.alertas_obsoletas.emit()
        self.vista.info(mensaje)

    def _eliminar(self, caso_uso, id_, panel, mensaje) -> None:
        if not self.vista.confirmar("¿Eliminar el registro seleccionado?"):
            return
        if self._intentar(lambda: caso_uso(id_) or True):
            panel.limpiar()
            self._tras_cambio(panel, mensaje)

    def _cargar_estacion(self, id_: int) -> None:
        e = next((x for x in self._layout.listar_estaciones(self.ctx.taller_id) if x.id == id_), None)
        if e:
            self.vista.estaciones.set_valores(vars(e), e.id)

    def _guardar_estacion(self, d: dict) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        funcion = d["funcion"] or "PROCESO"
        e = Estacion(tid, d["codigo"], d["nombre"], funcion, d["x"], d["y"],
                     d["tiempo_proceso_min"] if funcion == "PROCESO" else 0.0, d["capacidad"],
                     d["grupo"].strip().upper(), d["id"])
        g = self._intentar(self._layout.guardar_estacion, e)
        if g:
            self.vista.estaciones.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.estaciones, f"Estación «{g.codigo}» guardada.")

    def _cargar_conexion(self, id_: int) -> None:
        c = next((x for x in self._layout.listar_conexiones(self.ctx.taller_id) if x.id == id_), None)
        if c:
            self.vista.conexiones.set_valores(vars(c), c.id)

    def _guardar_conexion(self, d: dict) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        c = Conexion(tid, d["origen"] or "", d["destino"] or "", d["distancia_m"], d["ancho_m"],
                     d["bidireccional"], d["id"])
        g = self._intentar(self._layout.guardar_conexion, c)
        if g:
            self.vista.conexiones.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.conexiones, f"Conexión {g.origen}–{g.destino} guardada ({g.distancia_m:g} m).")

    def _cargar_prenda(self, id_: int) -> None:
        t = next((x for x in self._procesos.listar_tipos() if x.id == id_), None)
        if t:
            self.vista.prendas.set_valores(vars(t), t.id)

    def _guardar_prenda(self, d: dict) -> None:
        t = TipoPrenda(d["nombre"], d["peso_unidad_kg"], d["unidades_por_lote"], d["factor_proceso"], d["id"])
        g = self._intentar(self._procesos.guardar_tipo, t)
        if g:
            self.vista.prendas.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.prendas, f"Prenda «{g.nombre}» guardada.")

    def _cargar_ruta(self, id_: int) -> None:
        r = next((x for x in self._procesos.listar_rutas(self.ctx.taller_id) if x.id == id_), None)
        if r:
            self.vista.rutas.set_valores(vars(r), r.id)

    def _guardar_ruta(self, d: dict) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        r = RutaProceso(tid, d["tipo_prenda_id"] or 0, d["nombre"], d["fraccion_pct"], d["secuencia"], d["id"])
        g = self._intentar(self._procesos.guardar_ruta, r)
        if g:
            self.vista.rutas.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.rutas, f"Ruta «{g.nombre}» guardada.")

    def _cargar_pedido(self, id_: int) -> None:
        p = next((x for x in self._procesos.listar_pedidos(self.ctx.taller_id) if x.id == id_), None)
        if p:
            self.vista.pedidos.set_valores(vars(p), p.id)

    def _guardar_pedido(self, d: dict) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        p = Pedido(tid, d["tipo_prenda_id"] or 0, d["cantidad"], d["prioridad"], d["llegada_min"],
                   d["vencimiento_min"], d["origen_datos"] or "SINTETICO", d["id"])
        g = self._intentar(self._procesos.guardar_pedido, p)
        if g:
            self.vista.pedidos.set_valores(vars(g), g.id)
            self._tras_cambio(self.vista.pedidos, f"Pedido #{g.id} guardado.")

    def _calcular_ruta(self, origen: str, destino: str, ancho: float) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        if origen == destino:
            self.vista.error("Elija un origen y un destino distintos.")
            return
        ruta = self._intentar(self._layout.calcular_ruta, tid, origen, destino, ancho)
        if ruta is None:
            self._resaltar = frozenset()
            self.vista.mostrar_ruta(f"Sin ruta factible de {origen} a {destino}"
                                    + (f" con ancho mínimo {ancho:g} m." if ancho else "."), [])
        else:
            self._resaltar = frozenset(frozenset((t.origen, t.destino)) for t in ruta.tramos)
            self.vista.mostrar_ruta(
                f"Ruta: {' → '.join(ruta.nodos)}\nDistancia total: {ruta.distancia_m:g} m · Tramos: {len(ruta.tramos)}"
                f" · Ancho mínimo: {fmt(ruta.ancho_min_m)} m",
                [[i, f"{t.origen} → {t.destino}", fmt(t.distancia_m), fmt(t.ancho_m)]
                 for i, t in enumerate(ruta.tramos, 1)])
        self.vista.dibujar_red(*construir_red(self._layout, tid, self._resaltar, self.ctx.cerrados()))

    def _limpiar_ruta(self) -> None:
        self._resaltar = frozenset()
        self.vista.mostrar_ruta("Sin ruta activa.", [])
        self.vista.dibujar_red(*construir_red(self._layout, self.ctx.taller_id, cerrados=self.ctx.cerrados()))
