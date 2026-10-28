from ...domain.entities import MOTIVOS_CIERRE, Cierre
from ..theme import ROJO, TENUE, fmt
from .base import Controlador, construir_red, etiqueta_estacion


class ContingenciasController(Controlador):
    def __init__(self, vista, ctx, cierres, informe, exportar, simulacion, escenarios, layout):
        super().__init__(vista, ctx)
        self._cierres, self._informe, self._exportar_xlsx, self._sim = cierres, informe, exportar, simulacion
        self._esc, self._layout = escenarios, layout
        self._rutas = []
        p = vista.panel
        p.seleccionado.connect(self._cargar)
        p.guardar_solicitado.connect(self._guardar)
        p.eliminar_solicitado.connect(self._eliminar)
        vista.exportar_solicitado.connect(self._exportar)
        vista.ruta_elegida.connect(self._resaltar)
        vista.combo_escenario.currentIndexChanged.connect(lambda _: self._mostrar())

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        if tid is None:
            self.vista.panel.set_filas([], [])
            return
        ests = [e for e in self._layout.listar_estaciones(tid) if e.funcion not in ("ALMACEN", "DESPACHO")]
        nombres = {e.codigo: etiqueta_estacion(e) for e in ests}
        self.vista.panel.set_opciones("codigo", [(e.codigo, etiqueta_estacion(e)) for e in ests])
        cs = self._cierres.listar(tid)
        self.vista.panel.set_filas(
            [[c.id, nombres.get(c.codigo, c.codigo), MOTIVOS_CIERRE.get(c.motivo, c.motivo), fmt(c.desde_min, 0),
              fmt(c.hasta_min, 0) if c.hasta_min else "no reabre", "CERRADA" if c.vigente else "reabierta"] for c in cs],
            [c.id for c in cs], [ROJO if c.vigente else TENUE for c in cs])
        self.vista.set_escenarios([(e.id, e.nombre) for e in self._esc.listar(tid)])
        self._mostrar()

    def _cargar(self, id_: int) -> None:
        c = next((x for x in self._cierres.listar(self.ctx.taller_id) if x.id == id_), None)
        if c:
            self.vista.panel.set_valores(vars(c), c.id)

    def _guardar(self, d: dict) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        previo = next((x for x in self._cierres.listar(tid) if x.id == d["id"]), None)
        c = Cierre(tid, d["codigo"] or "", d["motivo"] or "OTRO", d["detalle"].strip(), d["desde_min"], d["hasta_min"],
                   d["bloquea_paso"], d["vigente"], previo.registrado if previo else "", d["id"])
        g = self._intentar(self._cierres.guardar, c)
        if g is None:
            return
        self.vista.panel.set_valores(vars(g), g.id)
        self._recalcular(f"Cierre de «{g.codigo}» guardado." if g.vigente else f"«{g.codigo}» quedó reabierta.")

    def _eliminar(self, id_: int) -> None:
        if self.vista.confirmar("¿Eliminar este registro de cierre? El área vuelve a operar."):
            self._cierres.eliminar(id_)
            self.vista.panel.limpiar()
            self._recalcular("Cierre eliminado.")

    def _recalcular(self, mensaje: str) -> None:
        tid = self.ctx.taller_id
        hechos = 0
        for e in self._esc.listar(tid):
            try:
                self._sim.execute(e.id, True)
                hechos += 1
            except Exception:
                pass
        self.refrescar()
        self.ctx.cierres_cambiaron.emit()
        self.vista.info(f"{mensaje} Se recalcularon rutas y {hechos} escenario(s).")

    def _mostrar(self) -> None:
        tid = self.ctx.taller_id
        v = self.vista
        v.mapa.dibujar(*construir_red(self._layout, tid, cerrados=self.ctx.cerrados()))
        self._rutas = []
        esc = v.combo_escenario.currentData()
        if esc and self.ctx.cerrados():
            try:
                self._rutas = self._informe.execute(esc).rutas
            except Exception:
                self._rutas = []
        v.tabla_rutas.set_filas([[f"{p} · {r}", b] for p, r, a, b, d0, d1, ok in self._rutas],
                                list(range(len(self._rutas))),
                                [None if x[6] else ROJO for x in self._rutas])
        if self._rutas:
            v.tabla_rutas.selectRow(0)
        else:
            v.mapa.limpiar_resaltes()

    def _resaltar(self, i: int) -> None:
        if 0 <= i < len(self._rutas):
            _, _, normal, alterna, _, _, ok = self._rutas[i]
            caminos = ([alterna.split(" → ")] if ok else []) + [normal.split(" → ")]
            self.vista.mapa.resaltar_caminos(caminos, 0 if ok else None)

    def _exportar(self, ruta: str, escenario_id: int) -> None:
        n = self._intentar(self._exportar_xlsx.execute, self.ctx.taller_id, escenario_id, ruta)
        if n:
            self.vista.info(f"Informe generado con {n} contingencia(s): {ruta}")
