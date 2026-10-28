from ...domain import normativa
from ...domain import analisis
from ...domain.alertas import Alerta, alertas_estaticas, alertas_prediccion, ordenar
from ..ports import EscenarioRepository, RegistroRepository
from .contexto import CargadorContexto
from .nucleo import exigir_simulable, simular_completo
from ..errors import ErrorDeNegocio


class ObtenerAlertas:

    def __init__(self, escenarios: EscenarioRepository, registros: RegistroRepository, ctx: CargadorContexto):
        self._esc, self._reg, self._ctx = escenarios, registros, ctx

    def execute(self, taller_id: int, simuladas_solo: bool = True) -> list[Alerta]:
        ctx = self._ctx.cargar(taller_id)
        escenarios = self._esc.list_by_taller(taller_id)
        cumpl = normativa.evaluar(ctx.par, ctx.taller, ctx.estaciones, ctx.conexiones, escenarios, ctx.robots)
        out = alertas_estaticas(ctx.estaciones, ctx.tipos, ctx.rutas, ctx.pedidos, cumpl)
        try:
            exigir_simulable(ctx)
        except ErrorDeNegocio:
            return ordenar(out)
        for e in escenarios:
            if simuladas_solo and not self._reg.list_by_escenario(e.id):
                # sin simular todavía: anticipo los cuellos con la carga ofrecida (cálculo analítico)
                carga = analisis.carga_ofrecida(ctx.estaciones_efectivas(), ctx.tipos, ctx.rutas, ctx.pedidos,
                                                e.tiempo_observacion_min, e.factor_demanda_pct)
                out += alertas_prediccion(ctx.par, e, ctx.estaciones_efectivas(), carga)
                continue
            out += simular_completo(ctx, e).alertas
        return ordenar(out)
