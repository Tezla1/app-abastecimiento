"""Traducciones de Qt al español: botones estándar (Sí/No/Cancelar/Aceptar), «Mostrar detalles…», diálogos de archivo, etc."""
from pathlib import Path

from PyQt6.QtCore import QLibraryInfo, QTranslator

_traductores: list = []     # deben seguir vivos mientras corre la aplicación


def _candidatos() -> list:
    raiz = Path(__file__).resolve().parents[2]        # carpeta del proyecto (o la temporal del .exe de un solo archivo)
    return [raiz / "assets" / "qt", Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))]


def instalar(app) -> bool:
    """Instala qtbase en español. Se busca primero la copia incluida con el programa y luego la de PyQt6."""
    for carpeta in _candidatos():
        t = QTranslator()
        if t.load("qtbase_es", str(carpeta)):
            app.installTranslator(t)
            _traductores.append(t)
            return True
    return False
