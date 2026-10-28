from dataclasses import dataclass, field


@dataclass(frozen=True)
class NodoVM:
    codigo: str
    nombre: str
    funcion: str
    x: float
    y: float
    cerrado: bool = False


@dataclass(frozen=True)
class ArcoVM:
    origen: str
    destino: str
    distancia_m: float
    resaltado: bool = False


@dataclass(frozen=True)
class CampoSpec:
    nombre: str
    etiqueta: str
    tipo: str = "text"
    minimo: float = 0
    maximo: float = 1_000_000
    decimales: int = 2
    defecto: object = None
    placeholder: str = ""
    ayuda: str = ""


@dataclass
class AnimacionVM:
    t_fin: float
    movimientos: list
    visitas: list
    capacidad: dict
    recursos: int
    inicio: str
    utilizacion: dict = field(default_factory=dict)
