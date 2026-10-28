# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Ejecuta las tareas largas en un hilo aparte, con barra de progreso y botón de cancelar, para que la ventana no se congele.

import os
import sys
from typing import Callable, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QProgressDialog

from ..application.errors import ErrorDeNegocio
from ..application.progreso import Cancelado

SINCRONO = os.environ.get("TEXTILFLOW_SINCRONO") == "1"
RETRASO_DIALOGO_MS = 400

_activas: list = []


def hay_tarea_activa() -> bool:
    return bool(_activas)


class _Hilo(QThread):
    avance = pyqtSignal(int, int, str)
    listo = pyqtSignal(object)
    fallo = pyqtSignal(object, object, object)
    cancelada = pyqtSignal()

    def __init__(self, funcion: Callable):
        super().__init__()
        self._funcion = funcion
        self._cancelar = False

    def pedir_cancelar(self) -> None:
        self._cancelar = True

    def _progreso(self, hecho: int, total: int, texto: str = "") -> None:
        if self._cancelar:
            raise Cancelado()
        self.avance.emit(hecho, total, texto)

    def run(self) -> None:
        try:
            self.listo.emit(self._funcion(self._progreso))
        except Cancelado:
            self.cancelada.emit()
        except BaseException as e:
            self.fallo.emit(type(e), e, e.__traceback__)


def ejecutar(parent, titulo: str, funcion: Callable[[Callable], object], al_terminar: Callable[[object], None],
             al_fallar: Optional[Callable[[BaseException], None]] = None, al_cancelar: Optional[Callable[[], None]] = None) -> None:
    def fallar(exc: BaseException, tb=None) -> None:
        if al_fallar is not None and isinstance(exc, ErrorDeNegocio):
            al_fallar(exc)
        elif isinstance(exc, ErrorDeNegocio) and al_fallar is None:
            raise exc
        else:
            sys.excepthook(type(exc), exc, tb or exc.__traceback__)

    if SINCRONO or QApplication.instance() is None:
        try:
            resultado = funcion(lambda *a: None)
        except Cancelado:
            if al_cancelar:
                al_cancelar()
            return
        except Exception as e:
            fallar(e)
            return
        al_terminar(resultado)
        return

    hilo = _Hilo(funcion)
    dlg = QProgressDialog(titulo, "Cancelar", 0, 0, parent)
    dlg.setWindowTitle("TextilFlow")
    dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
    dlg.setMinimumDuration(RETRASO_DIALOGO_MS)
    dlg.setAutoClose(False)
    dlg.setAutoReset(False)
    dlg.setMinimumWidth(380)

    def avance(hecho: int, total: int, texto: str) -> None:
        if total > 0:
            dlg.setMaximum(total)
            dlg.setValue(min(hecho, total))
        if texto:
            dlg.setLabelText(f"{titulo}\n{texto}")

    def cerrar() -> None:
        dlg.hide()
        dlg.deleteLater()
        if hilo in _activas:
            _activas.remove(hilo)
        hilo.deleteLater()

    def terminado(res) -> None:
        cerrar()
        al_terminar(res)

    def fallado(tipo, exc, tb) -> None:
        cerrar()
        fallar(exc, tb)

    def cancelado() -> None:
        cerrar()
        if al_cancelar:
            al_cancelar()

    dlg.canceled.connect(hilo.pedir_cancelar)
    dlg.canceled.connect(lambda: dlg.setLabelText("Cancelando…"))
    hilo.avance.connect(avance)
    hilo.listo.connect(terminado)
    hilo.fallo.connect(fallado)
    hilo.cancelada.connect(cancelado)
    _activas.append(hilo)
    hilo.start()
