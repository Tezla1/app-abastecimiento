from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


class AppContext(QObject):
    taller_activo_cambiado = pyqtSignal()
    talleres_cambiaron = pyqtSignal()
    cierres_cambiaron = pyqtSignal()
    alertas_obsoletas = pyqtSignal()     # los datos cambiaron: hay que recalcular la insignia de alertas

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
