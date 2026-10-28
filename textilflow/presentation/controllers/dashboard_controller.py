from ..theme import COLOR_NIVEL, fmt
from .base import Controlador, construir_red


class DashboardController(Controlador):
    def __init__(self, vista, ctx, dashboard, layout):
        super().__init__(vista, ctx)
        self._dashboard = dashboard
        self._layout = layout

    def refrescar(self) -> None:
        r = self._dashboard.execute(self.ctx.taller_id)
        self.vista.mostrar_kpis(r.talleres, r.estaciones, r.conexiones, r.pedidos, r.escenarios, len(r.alertas))
        self.vista.mostrar_indicadores(
            fmt(r.distancia_red_m, 1, " m") if r.conexiones else "—",
            fmt(r.ancho_min_m, 2, " m"),
            str(r.prendas) if r.prendas else "—",
            f"{r.escenarios_simulados} de {r.escenarios}",
        )
        self.vista.mostrar_actividad(r.actividad)
        vistas, top = set(), []
        for a in r.alertas:           # una fila por alerta distinta (cada escenario repite las suyas)
            k = (a.codigo, a.elemento)
            if k not in vistas:
                vistas.add(k)
                top.append(a)
        top = top[:7]
        self.vista.tabla_alertas.set_filas([[a.nivel, a.titulo] for a in top], colores=[COLOR_NIVEL.get(a.nivel) for a in top])
        self.vista.dibujar_red(*construir_red(self._layout, self.ctx.taller_id), r.trafico_arcos)
