from typing import Optional

from ...domain import analisis
from ..dto import ResultadoSimulacion


class ConsultarRutasNodo:
    """Qué rutas usarán los lotes que pasan por un nodo, según el pedido elegido."""

    def execute(self, resultado: ResultadoSimulacion, nodo: str, pedido_id: Optional[int] = None) -> list[dict]:
        return analisis.rutas_de_nodo(resultado.proceso, nodo, pedido_id)

    def trafico_hasta(self, resultado: ResultadoSimulacion, t_min: float):
        return analisis.trafico_hasta(resultado.proceso, t_min)
