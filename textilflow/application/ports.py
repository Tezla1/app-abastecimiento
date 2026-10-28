from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from ..domain.entities import (Cierre, Conexion, Escenario, Estacion, Parametro, Pedido, Registro,
                               Robot, RutaProceso, SolicitudCompra, Stock, Taller, TipoPrenda)

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    def add(self, entidad: T) -> T: ...

    @abstractmethod
    def update(self, entidad: T) -> T: ...

    @abstractmethod
    def get(self, id: int) -> Optional[T]: ...

    @abstractmethod
    def delete(self, id: int) -> None: ...

    @abstractmethod
    def list_all(self) -> list[T]: ...


class TallerRepository(Repository[Taller], ABC):
    pass


class RobotRepository(Repository[Robot], ABC):
    pass


class EstacionRepository(Repository[Estacion], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[Estacion]: ...


class ConexionRepository(Repository[Conexion], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[Conexion]: ...


class CierreRepository(Repository[Cierre], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[Cierre]: ...


class StockRepository(Repository[Stock], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[Stock]: ...


class SolicitudCompraRepository(Repository[SolicitudCompra], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[SolicitudCompra]: ...


class TipoPrendaRepository(Repository[TipoPrenda], ABC):
    pass


class RutaProcesoRepository(Repository[RutaProceso], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[RutaProceso]: ...


class PedidoRepository(Repository[Pedido], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[Pedido]: ...


class ParametroRepository(Repository[Parametro], ABC):
    pass


class EscenarioRepository(Repository[Escenario], ABC):
    @abstractmethod
    def list_by_taller(self, taller_id: int) -> list[Escenario]: ...


class RegistroRepository(Repository[Registro], ABC):
    @abstractmethod
    def list_by_escenario(self, escenario_id: int) -> list[Registro]: ...

    @abstractmethod
    def replace_for_escenario(self, escenario_id: int, registros: list[Registro]) -> None: ...


class SnapshotRepository(ABC):

    @abstractmethod
    def dump(self) -> dict: ...

    @abstractmethod
    def load(self, datos: dict) -> None: ...


@dataclass
class DatosExcel:
    taller: Optional[Taller] = None
    estaciones: list = field(default_factory=list)
    conexiones: list = field(default_factory=list)
    tipos: list = field(default_factory=list)
    rutas: list = field(default_factory=list)
    pedidos: list = field(default_factory=list)
    errores: list = field(default_factory=list)


class ExcelGateway(ABC):
    @abstractmethod
    def crear_plantilla(self, ruta: str) -> None: ...

    @abstractmethod
    def leer_taller(self, ruta: str) -> DatosExcel: ...

    @abstractmethod
    def escribir_taller(self, ruta: str, taller: Taller, estaciones: list, conexiones: list,
                        tipos: list, rutas: list, pedidos: list) -> None: ...


class ProyectoArchive(ABC):
    @abstractmethod
    def escribir(self, ruta: str, datos: dict) -> None: ...

    @abstractmethod
    def leer(self, ruta: str) -> dict: ...


class ExportadorReportes(ABC):
    @abstractmethod
    def exportar_csv(self, ruta: str, filas: list[dict]) -> None: ...

    @abstractmethod
    def exportar_xlsx(self, ruta: str, titulo: str, meta: list[tuple], filas: list[dict]) -> None: ...

    @abstractmethod
    def exportar_contingencias(self, ruta: str, titulo: str, cierres: list[dict], rutas: list[dict]) -> None: ...
