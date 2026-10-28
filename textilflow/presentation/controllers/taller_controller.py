from ...domain.entities import ORIGENES_DATOS, Taller
from ..theme import fmt
from .base import Controlador


class TallerController(Controlador):
    def __init__(self, vista, ctx, talleres):
        super().__init__(vista, ctx)
        self._talleres = talleres
        p = vista.panel
        p.seleccionado.connect(self._cargar)
        p.guardar_solicitado.connect(self._guardar)
        p.eliminar_solicitado.connect(self._eliminar)

    def refrescar(self) -> None:
        talleres = self._talleres.listar()
        self.vista.panel.set_filas(
            [[t.id, t.nombre, fmt(t.area_m2), t.operadores, fmt(t.jornada_h), ORIGENES_DATOS[t.origen_datos].upper()]
             for t in reversed(talleres)],
            [t.id for t in reversed(talleres)])

    def _cargar(self, taller_id: int) -> None:
        t = self._talleres.obtener(taller_id)
        if t:
            self.vista.panel.set_valores(vars(t), t.id)

    def _guardar(self, d: dict) -> None:
        t = Taller(d["nombre"], d["area_m2"], d["operadores"], d["jornada_h"],
                   d["origen_datos"] or "SINTETICO", d["observaciones"], d["id"])
        guardado = self._intentar(self._talleres.guardar, t)
        if guardado is None:
            return
        self.vista.panel.set_valores(vars(guardado), guardado.id)
        self.refrescar()
        self.vista.panel.tabla.seleccionar_id(guardado.id)
        self.vista.info(f"Taller «{guardado.nombre}» guardado.")
        self.ctx.talleres_cambiaron.emit()
        if self.ctx.taller_id is None:
            self.ctx.activar(guardado.id)

    def _eliminar(self, taller_id: int) -> None:
        t = self._talleres.obtener(taller_id)
        if t is None or not self.vista.confirmar(
                f"¿Eliminar el taller «{t.nombre}» con todo su layout, escenarios y registros?"):
            return
        if self._intentar(lambda: self._talleres.eliminar(taller_id) or True):
            self.vista.panel.limpiar()
            self.vista.info(f"Taller «{t.nombre}» eliminado.")
            self.ctx.talleres_cambiaron.emit()
