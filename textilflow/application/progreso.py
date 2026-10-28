"""Informe de avance y cancelación para operaciones largas (réplicas, barrido de flota, recálculos)."""
from typing import Callable, Optional

# progreso(hecho, total, texto) -> None; lanza Cancelado si el usuario pidió cancelar
Progreso = Optional[Callable[[int, int, str], None]]


class Cancelado(Exception):
    """El usuario canceló la operación; no es un error."""


def avisar(progreso: Progreso, hecho: int, total: int, texto: str = "") -> None:
    if progreso is not None:
        progreso(hecho, total, texto)
