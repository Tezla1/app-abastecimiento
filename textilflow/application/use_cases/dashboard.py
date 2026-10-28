from typing import Optional

from ..dto import ResumenDashboard
from ..errors import ErrorDeNegocio
from ..ports import (ConexionRepository, EscenarioRepository, EstacionRepository, PedidoRepository,
                     RegistroRepository, RutaProcesoRepository, TallerRepository, TipoPrendaRepository)
from .alertas import ObtenerAlertas
from .contexto import CargadorContexto
from .nucleo import simular_completo


class ObtenerDashboard:
    def __init__(self, talleres: TallerRepository, estaciones: EstacionRepository,
                 conexiones: ConexionRepository, tipos: TipoPrendaRepository, rutas: RutaProcesoRepository,
                 pedidos: PedidoRepository, escenarios: EscenarioRepository, registros: RegistroRepository,
                 alertas: ObtenerAlertas, ctx: CargadorContexto):
        self._t, self._est, self._con, self._tip, self._rut, self._ped = (
            talleres, estaciones, conexiones, tipos, rutas, pedidos)
        self._esc, self._reg, self._alertas, self._ctx = escenarios, registros, alertas, ctx

    def execute(self, taller_id: Optional[int]) -> ResumenDashboard:
        n_talleres = len(self._t.list_all())
        if taller_id is None or self._t.get(taller_id) is None:
            return ResumenDashboard(n_talleres, 0, 0, 0, 0, 0, 0, 0, 0.0, None,
                                    actividad=["Aún no hay un taller activo."])
        taller = self._t.get(taller_id)
        est = self._est.list_by_taller(taller_id)
        con = self._con.list_by_taller(taller_id)
        rutas = self._rut.list_by_taller(taller_id)
        ped = self._ped.list_by_taller(taller_id)
        esc = self._esc.list_by_taller(taller_id)
        simulados = [e for e in esc if self._reg.list_by_escenario(e.id)]
        traf = {}
        if simulados:   # mapa de calor del último escenario simulado
            try:
                traf = simular_completo(self._ctx.cargar(taller_id), simulados[-1]).trafico.arcos
            except ErrorDeNegocio:
                traf = {}
        actividad = [
            f"Taller activo · {taller.nombre}",
            f"Red · {len(est)} áreas / {len(con)} conexiones",
            f"Procesos · {len(self._tip.list_all())} prendas, {len(rutas)} ramas, {len(ped)} pedidos",
            f"Escenarios simulados · {len(simulados)} de {len(esc)}",
        ]
        return ResumenDashboard(
            talleres=n_talleres, estaciones=len(est), conexiones=len(con), prendas=len(self._tip.list_all()),
            rutas=len(rutas), pedidos=len(ped), escenarios=len(esc), escenarios_simulados=len(simulados),
            distancia_red_m=sum(c.distancia_m for c in con), ancho_min_m=min((c.ancho_m for c in con), default=None),
            alertas=self._alertas.execute(taller_id), trafico_arcos=traf, actividad=actividad)
