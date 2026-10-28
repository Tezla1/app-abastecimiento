from typing import Callable, Optional

from ...application.errors import ErrorDeNegocio
from ...domain.entities import FUNCIONES, ORIGENES_DATOS, TIPOS_ESCENARIO
from ..context import AppContext
from ..viewmodels import AnimacionVM, ArcoVM, NodoVM

ORIGENES_OPC = list(ORIGENES_DATOS.items())
FUNCIONES_OPC = list(FUNCIONES.items())
TIPOS_OPC = list(TIPOS_ESCENARIO.items())


class Controlador:
    """Intermediario vista ↔ casos de uso. La vista nunca llama a la aplicación directamente."""

    def __init__(self, vista, ctx: AppContext):
        self.vista = vista
        self.ctx = ctx

    def refrescar(self) -> None:
        pass

    def _intentar(self, accion: Callable, *args):
        """Ejecuta un caso de uso; los errores de negocio se muestran al usuario."""
        try:
            return accion(*args)
        except ErrorDeNegocio as e:
            self.vista.error(str(e))
        return None

    def _exigir_taller(self) -> Optional[int]:
        if self.ctx.taller_id is None:
            self.vista.error("Primero cree o seleccione un taller activo.")
        return self.ctx.taller_id


def etiqueta_estacion(e) -> str:
    return f"{e.codigo} · {e.nombre}" if e.nombre else e.codigo


def construir_red(layout, taller_id: Optional[int], resaltar=frozenset()):
    """Convierte la red del taller en view-models para el canvas 2D."""
    if taller_id is None:
        return [], []
    nodos = [NodoVM(e.codigo, e.nombre, e.funcion, e.x, e.y) for e in layout.listar_estaciones(taller_id)]
    arcos = [ArcoVM(c.origen, c.destino, c.distancia_m, frozenset((c.origen, c.destino)) in resaltar)
             for c in layout.listar_conexiones(taller_id)]
    return nodos, arcos


def construir_animacion(resultado, estaciones) -> AnimacionVM:
    """Convierte el resultado de una simulación en tuplas planas para el mapa animado."""
    p = resultado.proceso
    return AnimacionVM(
        t_fin=max(p.t_fin_min, 1.0),
        movimientos=[(m.recurso, m.t0, m.t1, tuple(m.ruta), m.cargado, m.kg) for m in p.movimientos],
        visitas=[(v.estacion, v.llegada_min, v.inicio_min, v.fin_min) for v in p.visitas],
        capacidad={e.codigo: e.capacidad for e in estaciones if e.tiempo_proceso_min > 0},
        recursos=p.params.num_recursos, inicio=p.params.nodo_inicial,
        utilizacion={s.codigo: s.utilizacion_pct for s in resultado.estados})
