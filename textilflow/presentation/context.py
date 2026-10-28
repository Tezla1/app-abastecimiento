from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


class AppContext(QObject):
    taller_activo_cambiado = pyqtSignal()
    talleres_cambiaron = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.taller_id: Optional[int] = None

    def activar(self, taller_id: Optional[int]) -> None:
        if taller_id != self.taller_id:
            self.taller_id = taller_id
            self.taller_activo_cambiado.emit()
