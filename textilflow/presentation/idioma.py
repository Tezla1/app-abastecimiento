from pathlib import Path

from PyQt6.QtCore import QLibraryInfo, QTranslator

_traductores: list = []


def _candidatos() -> list:
    raiz = Path(__file__).resolve().parents[2]
    return [raiz / "assets" / "qt", Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))]


def instalar(app) -> bool:
    for carpeta in _candidatos():
        t = QTranslator()
        if t.load("qtbase_es", str(carpeta)):
            app.installTranslator(t)
            _traductores.append(t)
            return True
    return False
