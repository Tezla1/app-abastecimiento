# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Estado compartido entre pantallas: taller activo, cierres vigentes y avisos de que los datos o las alertas cambiaron.

from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


class ContextoApp(QObject):
    taller_activo_cambiado = pyqtSignal()
    talleres_cambiaron = pyqtSignal()
    cierres_cambiaron = pyqtSignal()
    alertas_obsoletas = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.taller_id: Optional[int] = None
        self.proveedor_cerrados = lambda taller_id: frozenset()
        self.cierres_cambiaron_senal = None

    def cerrados(self) -> frozenset:
        return self.proveedor_cerrados(self.taller_id)

    def activar(self, taller_id: Optional[int]) -> None:
        if taller_id != self.taller_id:
            self.taller_id = taller_id
            self.taller_activo_cambiado.emit()
