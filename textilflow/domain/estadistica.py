"""Estadística descriptiva para las réplicas (media, desviación, IC 95 %)."""
import math
from dataclasses import dataclass
from typing import Optional, Sequence

# t de Student bilateral 95 % para gl = 1..30; después se usa la normal (1,96).
_T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145,
        2.131, 2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048,
        2.045, 2.042]


def t_critico_95(gl: int) -> float:
    return _T95[gl - 1] if 1 <= gl <= 30 else 1.96


@dataclass
class Resumen:
    n: int
    media: Optional[float]
    desv: Optional[float]
    minimo: Optional[float]
    maximo: Optional[float]
    ic_inf: Optional[float]
    ic_sup: Optional[float]


def resumir(valores: Sequence[Optional[float]]) -> Resumen:
    """Ignora los None (réplicas donde el indicador no se pudo calcular)."""
    xs = [v for v in valores if v is not None]
    n = len(xs)
    if n == 0:
        return Resumen(0, None, None, None, None, None, None)
    media = sum(xs) / n
    if n == 1:
        return Resumen(1, media, None, media, media, None, None)   # con una muestra no hay dispersión
    desv = math.sqrt(sum((x - media) ** 2 for x in xs) / (n - 1))
    mitad = t_critico_95(n - 1) * desv / math.sqrt(n)
    return Resumen(n, media, desv, min(xs), max(xs), media - mitad, media + mitad)


def histograma(valores: Sequence[float], clases: int = 10) -> list[tuple]:
    """[(límite_inf, límite_sup, frecuencia)]."""
    xs = list(valores)
    if not xs:
        return []
    lo, hi = min(xs), max(xs)
    if hi == lo:
        return [(lo, hi, len(xs))]
    ancho = (hi - lo) / clases
    cuentas = [0] * clases
    for x in xs:
        cuentas[min(int((x - lo) / ancho), clases - 1)] += 1
    return [(lo + i * ancho, lo + (i + 1) * ancho, c) for i, c in enumerate(cuentas)]
