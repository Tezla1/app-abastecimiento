from ...domain import normativa
from ..errors import ErrorDeNegocio
from ..ports import (ConexionRepository, EstacionRepository, ParametroRepository, PedidoRepository,
                     RobotRepository, RutaProcesoRepository, TallerRepository, TipoPrendaRepository)
from .nucleo import Contexto


class CargadorContexto:
    """Reúne en memoria todo lo que necesita un cálculo sobre un taller."""

    def __init__(self, talleres: TallerRepository, estaciones: EstacionRepository,
                 conexiones: ConexionRepository, tipos: TipoPrendaRepository,
                 rutas: RutaProcesoRepository, pedidos: PedidoRepository,
                 robots: RobotRepository, parametros: ParametroRepository):
        self._t, self._est, self._con = talleres, estaciones, conexiones
        self._tipos, self._rut, self._ped = tipos, rutas, pedidos
        self._rob, self._par = robots, parametros

    def parametros(self) -> dict:
        return normativa.valores(self._par.list_all())

    def cargar(self, taller_id: int) -> Contexto:
        taller = self._t.get(taller_id)
        if taller is None:
            raise ErrorDeNegocio("Seleccione un taller.")
        return Contexto(
            taller, self._est.list_by_taller(taller_id), self._con.list_by_taller(taller_id),
            sorted(self._tipos.list_all(), key=lambda t: t.id or 0),
            self._rut.list_by_taller(taller_id), self._ped.list_by_taller(taller_id),
            self._rob.list_all(), self.parametros())
