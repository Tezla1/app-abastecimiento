# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Crear, validar y borrar escenarios de simulación.

from ...domain.entities import Escenario
from ..errors import ErrorDeNegocio
from ..ports import EscenarioRepository, EstacionRepository, RobotRepository
from .talleres import exigir_valido


class GestionarEscenarios:
    def __init__(self, escenarios: EscenarioRepository, estaciones: EstacionRepository,
                 robots: RobotRepository):
        self._esc = escenarios
        self._est = estaciones
        self._robots = robots

    def listar(self, taller_id: int) -> list[Escenario]:
        return sorted(self._esc.list_by_taller(taller_id), key=lambda e: e.id or 0)

    def obtener(self, escenario_id: int) -> Escenario:
        e = self._esc.get(escenario_id)
        if e is None:
            raise ErrorDeNegocio("El escenario ya no existe.")
        return e

    def guardar(self, e: Escenario) -> Escenario:
        exigir_valido(e)
        if e.nodo_inicial not in {s.codigo for s in self._est.list_by_taller(e.taller_id)}:
            raise ErrorDeNegocio(f"El nodo inicial «{e.nodo_inicial}» no existe en el taller.")
        if e.tipo != "AMR":
            e.robot_id = None
        elif e.robot_id:
            robot = self._robots.get(e.robot_id)
            if robot is None:
                raise ErrorDeNegocio("El robot seleccionado ya no existe.")
            e.velocidad_ms, e.capacidad_kg = robot.velocidad_ms, robot.capacidad_kg
        return self._esc.update(e) if e.id else self._esc.add(e)

    def eliminar(self, escenario_id: int) -> None:
        self._esc.delete(escenario_id)
