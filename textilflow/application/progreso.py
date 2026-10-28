# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Aviso de avance para las tareas largas y la excepción que las cancela.

from typing import Callable, Optional

Progreso = Optional[Callable[[int, int, str], None]]


class Cancelado(Exception):
    pass


def avisar(progreso: Progreso, hecho: int, total: int, texto: str = "") -> None:
    if progreso is not None:
        progreso(hecho, total, texto)
