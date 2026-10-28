import sys
import threading
import time

from PyQt6.QtCore import QObject, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QGuiApplication
from PyQt6.QtWidgets import QApplication, QMessageBox

from .. import registro


class _Puente(QObject):
    error = pyqtSignal(object, object, object)


_puente = None
_ultimo = (None, 0.0)
_mostrando = False


def mostrar(d: dict, parent=None) -> str:
    caja = QMessageBox(parent)
    caja.setIcon(QMessageBox.Icon.Warning)
    caja.setWindowTitle("TextilFlow · " + d["titulo"])
    caja.setText(f"<b>{d['titulo']}</b>")
    caja.setInformativeText(f"<b>Qué pasó:</b> {d['que']}<br><b>Dónde:</b> {d['donde']}<br><b>Qué hacer:</b> {d['sugerencia']}"
                            f"<br><br><span style='color:gray'>Detalle guardado en: {registro.ruta_log()}</span>")
    caja.setDetailedText(d["resumen"] + "\n\n" + d["detalle"])
    seguir = caja.addButton("Continuar", QMessageBox.ButtonRole.AcceptRole)
    copiar = caja.addButton("Copiar detalle", QMessageBox.ButtonRole.ActionRole)
    carpeta = caja.addButton("Abrir carpeta del registro", QMessageBox.ButtonRole.ActionRole)
    cerrar = caja.addButton("Cerrar programa", QMessageBox.ButtonRole.DestructiveRole)
    caja.setDefaultButton(seguir)
    while True:
        caja.exec()
        b = caja.clickedButton()
        if b is copiar:
            QGuiApplication.clipboard().setText(registro.informe_texto(d))
            continue
        if b is carpeta:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(registro.ruta_log().parent)))
            continue
        return "cerrar" if b is cerrar else "seguir"


def _manejar(tipo, exc, tb) -> None:
    global _ultimo, _mostrando
    if issubclass(tipo, KeyboardInterrupt):
        sys.__excepthook__(tipo, exc, tb)
        return
    d = registro.describir(tipo, exc, tb)
    registro.registrar(f"Error no controlado en {d['donde']}", exc)
    app = QApplication.instance()
    clave, t = _ultimo
    if app is None or _mostrando or (clave == d["resumen"] and time.monotonic() - t < 2.0):
        return
    _ultimo = (d["resumen"], time.monotonic())
    _mostrando = True
    try:
        accion = mostrar(d, app.activeWindow())
    finally:
        _mostrando = False
    if accion == "cerrar":
        app.quit()


def instalar() -> None:
    global _puente
    _puente = _Puente()
    _puente.error.connect(_manejar, Qt.ConnectionType.QueuedConnection)
    sys.excepthook = _manejar

    def _en_hilo(args):
        _puente.error.emit(args.exc_type, args.exc_value, args.exc_traceback)
    threading.excepthook = _en_hilo
