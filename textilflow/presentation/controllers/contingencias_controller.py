from pathlib import Path

from ...application.informe_html import informe_a_html
from ...domain.entities import MOTIVOS_CIERRE, Cierre
from ..theme import ROJO, TENUE, fmt
from .base import Controlador, etiqueta_estacion


class ContingenciasController(Controlador):
    def __init__(self, vista, ctx, cierres, informe, simulacion, escenarios, layout):
        super().__init__(vista, ctx)
        self._cierres, self._informe, self._sim = cierres, informe, simulacion
        self._esc, self._layout = escenarios, layout
        self._html = ""
        p = vista.panel
        p.seleccionado.connect(self._cargar)
        p.guardar_solicitado.connect(self._guardar)
        p.eliminar_solicitado.connect(self._eliminar)
        vista.informe_solicitado.connect(self._generar)
        vista.exportar_solicitado.connect(self._exportar)

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
        if self.vista.combo_escenario.currentData():
            self._generar(self.vista.combo_escenario.currentData(), silencioso=True)

    def _generar(self, escenario_id: int, silencioso: bool = False) -> None:
        if not escenario_id:
            self.vista.error("Cree un escenario en «Escenarios y simulación» para generar el informe.")
            return
        try:
            inf = self._informe.execute(escenario_id)
        except Exception as e:
            if not silencioso:
                self.vista.error(str(e))
            else:
                self.vista.navegador.setHtml(f"<p style='color:#6B7A90'>{e}</p>")
            return
        self._html = informe_a_html(inf)
        self.vista.mostrar_informe(self._html)

    def _exportar(self, ruta: str) -> None:
        if self._html:
            Path(ruta).write_text(self._html, encoding="utf-8")
            self.vista.info(f"Informe guardado en {ruta}")
