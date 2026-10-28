from typing import Optional

from ...domain.entities import Taller
from ..errors import ErrorDeNegocio
from ..ports import TallerRepository


def exigir_valido(entidad) -> None:
    errores = entidad.validar()
    if errores:
        raise ErrorDeNegocio(" ".join(errores))


class GestionarTalleres:
    def __init__(self, talleres: TallerRepository):
        self._talleres = talleres

    def listar(self) -> list[Taller]:
        return sorted(self._talleres.list_all(), key=lambda t: t.id or 0)

    def obtener(self, taller_id: int) -> Optional[Taller]:
        return self._talleres.get(taller_id)

    def guardar(self, taller: Taller) -> Taller:
        exigir_valido(taller)
        taller.nombre = taller.nombre.strip()
        return self._talleres.update(taller) if taller.id else self._talleres.add(taller)

    def eliminar(self, taller_id: int) -> None:
        if self._talleres.get(taller_id) is None:
            raise ErrorDeNegocio("El taller ya no existe.")
        self._talleres.delete(taller_id)  # estaciones, conexiones, etc. caen en cascada
