# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Validación integral: revisa que los datos y el modelo sean coherentes antes de usar los resultados.

from ...domain import normativa
from ...domain.validacion import ContextoValidacion, Hallazgo, validar
from ..errors import ErrorDeNegocio
from ..ports import (ConexionRepository, EscenarioRepository, EstacionRepository, ParametroRepository,
                     PedidoRepository, RegistroRepository, RobotRepository, RutaProcesoRepository,
                     TallerRepository, TipoPrendaRepository)


class ValidarProyecto:
    def __init__(self, talleres: TallerRepository, estaciones: EstacionRepository,
                 conexiones: ConexionRepository, tipos: TipoPrendaRepository,
                 rutas: RutaProcesoRepository, pedidos: PedidoRepository, robots: RobotRepository,
                 escenarios: EscenarioRepository, registros: RegistroRepository,
                 parametros: ParametroRepository):
        self._t, self._est, self._con = talleres, estaciones, conexiones
        self._tip, self._rut, self._ped = tipos, rutas, pedidos
        self._rob, self._esc, self._reg, self._par = robots, escenarios, registros, parametros

    def execute(self, taller_id: int) -> list[Hallazgo]:
        taller = self._t.get(taller_id)
        if taller is None:
            raise ErrorDeNegocio("Seleccione un taller para validar.")
        escenarios = self._esc.list_by_taller(taller_id)
        par = normativa.valores(self._par.list_all())
        ctx = ContextoValidacion(
            taller=taller,
            estaciones=self._est.list_by_taller(taller_id),
            conexiones=self._con.list_by_taller(taller_id),
            tipos=self._tip.list_all(),
            rutas=self._rut.list_by_taller(taller_id),
            pedidos=self._ped.list_by_taller(taller_id),
            robots=self._rob.list_all(),
            escenarios=escenarios,
            registros={e.id: self._reg.list_by_escenario(e.id) for e in escenarios},
            holgura_robot_m=par["holgura_lateral_robot_m"],
        )
        return validar(ctx)
