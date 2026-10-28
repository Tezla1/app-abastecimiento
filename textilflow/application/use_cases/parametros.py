# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Lee, cambia y restaura los parámetros normativos y de diseño.

from ...domain import normativa
from ...domain.entities import Parametro
from ..errors import ErrorDeNegocio
from ..ports import ParametroRepository


class GestionarParametros:
    def __init__(self, repo: ParametroRepository):
        self._repo = repo

    def listar(self) -> list[Parametro]:
        existentes = {p.clave: p for p in self._repo.list_all()}
        for d in normativa.PARAMETROS_DEFECTO:
            if d.clave not in existentes:
                existentes[d.clave] = self._repo.add(Parametro(d.clave, d.valor, d.unidad, d.descripcion,
                                                               d.fuente, d.verificado))
        orden = {d.clave: i for i, d in enumerate(normativa.PARAMETROS_DEFECTO)}
        return sorted(existentes.values(), key=lambda p: orden.get(p.clave, 999))

    def valores(self) -> dict:
        return normativa.valores(self.listar())

    def cambiar_valor(self, clave: str, valor: float) -> Parametro:
        p = next((x for x in self.listar() if x.clave == clave), None)
        if p is None:
            raise ErrorDeNegocio(f"Parámetro desconocido: {clave}.")
        if valor <= 0:
            raise ErrorDeNegocio("El valor debe ser mayor que 0.")
        p.valor = float(valor)
        return self._repo.update(p)

    def restaurar(self) -> None:
        for p in self.listar():
            d = next(x for x in normativa.PARAMETROS_DEFECTO if x.clave == p.clave)
            p.valor = d.valor
            self._repo.update(p)
