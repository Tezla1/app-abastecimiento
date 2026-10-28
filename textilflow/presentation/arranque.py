import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QLockFile, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox

from .. import registro
from ..container import Contenedor, construir


def _caja(titulo, texto, icono=QMessageBox.Icon.Warning, detalle="") -> QMessageBox:
    c = QMessageBox()
    c.setIcon(icono)
    c.setWindowTitle(f"TextilFlow · {titulo}")
    c.setText(f"<b>{titulo}</b>")
    c.setInformativeText(texto)
    if detalle:
        c.setDetailedText(detalle)
    return c


class InstanciaUnica:

    def __init__(self):
        self._lock = None

    def tomar(self) -> bool:
        carpeta = registro.carpeta_datos()
        carpeta.mkdir(parents=True, exist_ok=True)
        self._lock = QLockFile(str(carpeta / "textilflow.lock"))
        if self._lock.tryLock(100):
            return True
        caja = _caja("TextilFlow ya está abierto",
                     "Ya hay otra ventana de TextilFlow usando sus datos. Abrir una segunda podría dañar el archivo.<br>"
                     "Búsquela en la barra de tareas o ciérrela y vuelva a intentarlo.", QMessageBox.Icon.Information)
        caja.exec()
        return False

    def soltar(self) -> None:
        if self._lock is not None:
            self._lock.unlock()


def _revisar(c: Contenedor) -> None:
    ok = c.db.conn.execute("PRAGMA quick_check").fetchone()[0]
    if ok != "ok":
        raise sqlite3.DatabaseError(f"La verificación de integridad devolvió: {ok}")


def abrir_contenedor(ruta: str) -> Contenedor | None:
    try:
        c = construir(ruta)
        if ruta != ":memory:":
            _revisar(c)
        return c
    except (sqlite3.Error, OSError) as e:
        registro.registrar(f"No se pudo abrir la base de datos {ruta}", e)
        d = registro.describir(type(e), e, e.__traceback__)
        caja = _caja("No se pudo abrir la base de datos",
                     f"{d['que']}<br><br><b>Archivo:</b> {ruta}<br><b>Técnico:</b> {d['resumen']}<br><br>"
                     "«Empezar con una base nueva» guarda una copia del archivo con problemas "
                     "(termina en <i>.danada.bak</i>) y crea una base nueva con datos de ejemplo. "
                     "La copia no se borra: se puede recuperar después.", detalle=d["detalle"])
        nueva = caja.addButton("Empezar con una base nueva", QMessageBox.ButtonRole.AcceptRole)
        carpeta = caja.addButton("Abrir carpeta de datos", QMessageBox.ButtonRole.ActionRole)
        salir = caja.addButton("Salir", QMessageBox.ButtonRole.RejectRole)
        caja.setDefaultButton(nueva)
        while True:
            caja.exec()
            b = caja.clickedButton()
            if b is carpeta:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(ruta).parent)))
                continue
            break
        if b is salir or b is not nueva:
            return None
        p = Path(ruta)
        destino = p.with_suffix(f".{datetime.now():%Y%m%d_%H%M%S}.danada.bak")
        try:
            if p.exists():
                shutil.move(str(p), str(destino))
            c = construir(ruta)
            c.demo.execute()
            return c
        except (sqlite3.Error, OSError) as e2:
            registro.registrar("Tampoco se pudo crear una base nueva", e2)
            _caja("No se pudo crear la base nueva",
                  f"Revise que tenga permiso para escribir en la carpeta:<br>{p.parent}<br><br>{e2}").exec()
            return None


def avisar_migracion(c: Contenedor) -> None:
    if getattr(c.db, "respaldo_v1", ""):
        caja = _caja("Se actualizó el formato de sus datos",
                     "Se encontró una base de datos de una versión muy anterior de TextilFlow, que no es compatible "
                     "con esta. No se perdió nada: se guardó una copia en<br>"
                     f"<b>{c.db.respaldo_v1}</b><br>y se creó una base nueva con datos de ejemplo.",
                     QMessageBox.Icon.Information)
        caja.exec()


def ofrecer_recuperacion(c: Contenedor) -> bool:
    r = c.respaldos
    if not r.sesion_anterior_incorrecta():
        return False
    lista = r.listar()
    if not lista:
        return False
    ruta, fecha = lista[0]
    caja = _caja("La última sesión no se cerró correctamente",
                 "TextilFlow se cerró de forma inesperada (cierre forzado, corte de energía o apagado del equipo). "
                 "Sus datos se guardan a medida que trabaja, así que normalmente no se perdió nada.<br><br>"
                 f"Hay un respaldo automático del <b>{fecha:%d/%m/%Y %H:%M}</b>. ¿Desea restaurarlo?<br>"
                 "<i>Restaurar reemplaza los datos actuales por los del respaldo.</i>", QMessageBox.Icon.Question)
    si = caja.addButton("Restaurar ese respaldo", QMessageBox.ButtonRole.DestructiveRole)
    no = caja.addButton("Continuar con mis datos actuales", QMessageBox.ButtonRole.AcceptRole)
    caja.setDefaultButton(no)
    caja.exec()
    if caja.clickedButton() is si:
        try:
            r.restaurar(ruta)
            c.db.marcar_guardado()
            return True
        except Exception as e:
            registro.registrar("No se pudo restaurar el respaldo automático", e)
            _caja("No se pudo restaurar", f"El respaldo no se pudo leer: {e}").exec()
    return False
