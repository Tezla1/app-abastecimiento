"""Estructuras planas que la vista sabe dibujar (la vista no conoce entidades de dominio)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NodoVM:
    codigo: str
    nombre: str
    funcion: str
    x: float
    y: float


@dataclass(frozen=True)
class ArcoVM:
    origen: str
    destino: str
    distancia_m: float
    resaltado: bool = False


@dataclass(frozen=True)
class CampoSpec:
    """Describe un campo de formulario de un CrudPanel."""
    nombre: str
    etiqueta: str
    tipo: str = "text"  # text | multiline | int | float | combo | check
    minimo: float = 0
    maximo: float = 1_000_000
    decimales: int = 2
    defecto: object = None
    placeholder: str = ""


@dataclass
class AnimacionVM:
    """Todo lo que el mapa necesita para animar una simulación (tuplas planas, sin entidades)."""
    t_fin: float
    movimientos: list      # (recurso, t0, t1, ruta, cargado, kg)
    visitas: list          # (estacion, llegada, inicio|None, fin|None)
    capacidad: dict        # estación -> puestos
    recursos: int
    inicio: str
    utilizacion: dict = field(default_factory=dict)   # estación -> % (simulada)
