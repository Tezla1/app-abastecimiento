from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


class AppContext(QObject):
    """Estado compartido de la interfaz: taller activo y avisos de cambios."""
    taller_activo_cambiado = pyqtSignal()
    talleres_cambiaron = pyqtSignal()   # se creó / editó / eliminó algún taller

    def __init__(self):
        super().__init__()
        self.taller_id: Optional[int] = None

    def activar(self, taller_id: Optional[int]) -> None:
        if taller_id != self.taller_id:
            self.taller_id = taller_id
            self.taller_activo_cambiado.emit()
