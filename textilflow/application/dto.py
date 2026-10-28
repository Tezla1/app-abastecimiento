# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Estructuras simples con los resultados que los casos de uso devuelven a la interfaz (simulación, comparación, réplicas, barridos).

from dataclasses import dataclass, field
from typing import Optional

from ..domain.entities import Escenario, Robot


@dataclass
class ResultadoSimulacion:
    escenario: Escenario
    proceso: object
    registros: list
    indicadores: dict
    ind: object
    estados: list
    carga: dict
    trafico: object
    series: dict
    alertas: list
    flota: dict
    recorridos: dict
    prendas: dict = field(default_factory=dict)


@dataclass
class DetalleIndicadores:
    escenario: Escenario
    registros: list
    indicadores: dict


@dataclass
class ResultadoComparacion:
    base: Escenario
    alternativo: Escenario
    ind_base: dict
    ind_alt: dict
    comparable: bool
    problemas: list
    filas: list
    filas_proceso: list = field(default_factory=list)
    series_base: dict = field(default_factory=dict)
    series_alt: dict = field(default_factory=dict)


@dataclass
class CompatibilidadRobot:
    robot: Robot
    ancho_requerido_m: float
    ancho_min_red_m: Optional[float]
    arcos_estrechos: list
    peso_unidad_max_kg: float
    prendas_excedidas: list
    compatible_ancho: bool
    compatible_carga: bool
    mensajes: list = field(default_factory=list)


@dataclass
class ResultadoReplicas:
    escenario: Escenario
    n: int
    filas: list
    resumen: dict
    nota: str = ""


@dataclass
class FilaBarrido:
    recursos: int
    utilizacion_pct: Optional[float]
    espera_prom_min: Optional[float]
    completados_pct: float
    lead_time_min: Optional[float]
    makespan_min: float
    a_tiempo_pct: Optional[float]
    cumple: bool = False


@dataclass
class Requerimientos:
    escenario: Escenario
    criticos: list
    ramas: list
    recorridos: dict
    flota: dict
    barrido: list
    recomendado: Optional[int]
    viajes_por_prenda: list
    cumplimientos: list
    estados: list
    notas: list = field(default_factory=list)


@dataclass
class ResumenDashboard:
    talleres: int
    estaciones: int
    conexiones: int
    prendas: int
    rutas: int
    pedidos: int
    escenarios: int
    escenarios_simulados: int
    distancia_red_m: float
    ancho_min_m: Optional[float]
    alertas: list = field(default_factory=list)
    trafico_arcos: dict = field(default_factory=dict)
    actividad: list = field(default_factory=list)
