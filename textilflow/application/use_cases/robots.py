from ...domain import normativa
from ...domain.entities import Robot
from ..dto import CompatibilidadRobot
from ..errors import ErrorDeNegocio
from ..ports import ConexionRepository, ParametroRepository, RobotRepository, TipoPrendaRepository
from .talleres import exigir_valido


class GestionarRobots:
    def __init__(self, robots: RobotRepository, conexiones: ConexionRepository,
                 tipos: TipoPrendaRepository, parametros: ParametroRepository):
        self._robots = robots
        self._con = conexiones
        self._tipos = tipos
        self._par = parametros

    def listar(self) -> list[Robot]:
        return sorted(self._robots.list_all(), key=lambda r: r.id or 0)

    def guardar(self, robot: Robot) -> Robot:
        exigir_valido(robot)
        robot.nombre = robot.nombre.strip()
        return self._robots.update(robot) if robot.id else self._robots.add(robot)

    def eliminar(self, robot_id: int) -> None:
        self._robots.delete(robot_id)

    def evaluar_compatibilidad(self, taller_id: int, robot_id: int) -> CompatibilidadRobot:
        """Compatibilidad geométrica y de carga robot ↔ taller (no es certificación de seguridad)."""
        robot = self._robots.get(robot_id)
        if robot is None:
            raise ErrorDeNegocio("Seleccione un robot válido.")
        par = normativa.valores(self._par.list_all())
        req = normativa.ancho_requerido_robot(robot, par)
        conexiones = self._con.list_by_taller(taller_id)
        tipos = self._tipos.list_all()
        estrechos = [f"{c.origen}–{c.destino} ({c.ancho_m:g} m)" for c in conexiones if c.ancho_m < req]
        ancho_min = min((c.ancho_m for c in conexiones), default=None)
        peso_max = max((t.peso_unidad_kg for t in tipos), default=0.0)
        excedidas = [t.nombre for t in tipos if t.peso_unidad_kg > robot.capacidad_kg]
        msgs = []
        if not conexiones:
            msgs.append("El taller no tiene conexiones registradas: no se puede evaluar el ancho.")
        elif estrechos:
            msgs.append(f"El robot necesita {req:.2f} m libres ({robot.ancho_m:g} m + holgura): "
                        f"{len(estrechos)} pasillo(s) quedan vetados: " + ", ".join(estrechos) + ".")
        else:
            msgs.append(f"El robot necesita {req:.2f} m y cabe en todos los pasillos (mínimo {ancho_min:g} m).")
        if excedidas:
            msgs.append("Una unidad de " + ", ".join(excedidas) + f" supera los {robot.capacidad_kg:g} kg del robot.")
        elif tipos:
            msgs.append(f"La capacidad cubre al menos una unidad de cualquier prenda (máx. {peso_max:g} kg).")
        return CompatibilidadRobot(robot, req, ancho_min, estrechos, peso_max, excedidas,
                                   bool(conexiones) and not estrechos, not excedidas, msgs)
