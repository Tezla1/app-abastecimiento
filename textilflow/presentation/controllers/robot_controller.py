# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Controlador del diseño conceptual del robot: perfiles y compatibilidad con los pasillos.

from ...domain.entities import ORIGENES_DATOS, Robot
from ..theme import fmt
from .base import Controlador


class RobotController(Controlador):
    def __init__(self, vista, ctx, robots):
        super().__init__(vista, ctx)
        self._robots = robots
        p = vista.panel
        p.seleccionado.connect(self._cargar)
        p.guardar_solicitado.connect(self._guardar)
        p.eliminar_solicitado.connect(self._eliminar)
        vista.evaluar_solicitado.connect(self._evaluar)

    def refrescar(self) -> None:
        rs = self._robots.listar()
        self.vista.panel.set_filas(
            [[r.id, r.nombre, fmt(r.capacidad_kg), fmt(r.velocidad_ms, 3), fmt(r.ancho_m, 3),
              fmt(r.radio_giro_m, 3), ORIGENES_DATOS[r.origen_datos].upper()] for r in rs], [r.id for r in rs])
        self.vista.set_robots([(r.id, f"{r.nombre} · {r.capacidad_kg:g} kg · {r.ancho_m:g} m") for r in rs])

    def _cargar(self, id_: int) -> None:
        r = next((x for x in self._robots.listar() if x.id == id_), None)
        if r:
            self.vista.panel.set_valores(vars(r), r.id)

    def _guardar(self, d: dict) -> None:
        r = Robot(d["nombre"], d["capacidad_kg"], d["velocidad_ms"], d["ancho_m"], d["radio_giro_m"],
                  d["origen_datos"] or "DISENO", d["id"])
        g = self._intentar(self._robots.guardar, r)
        if g:
            self.vista.panel.set_valores(vars(g), g.id)
            self.refrescar()
            self.vista.info(f"Robot «{g.nombre}» guardado.")

    def _eliminar(self, id_: int) -> None:
        if self.vista.confirmar("¿Eliminar este perfil de robot? Los escenarios que lo usan quedarán sin robot."):
            self._robots.eliminar(id_)
            self.vista.panel.limpiar()
            self.refrescar()
            self.vista.info("Robot eliminado.")

    def _evaluar(self, robot_id: int) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        c = self._intentar(self._robots.evaluar_compatibilidad, tid, robot_id)
        if c is None:
            return
        marca = lambda ok: "✔" if ok else "✖"
        self.vista.mostrar_evaluacion(
            f"<b>{c.robot.nombre}</b><br>"
            f"{marca(c.compatible_ancho)} Ancho &nbsp;&nbsp; {marca(c.compatible_carga)} Carga<br>"
            + "<br>".join(f"• {m}" for m in c.mensajes))
