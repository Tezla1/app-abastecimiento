"""Registro de errores en archivo (textilflow.log) y descripción en lenguaje claro de las excepciones.

No depende de Qt: lo usan tanto la ventana de error como los bloques que antes ignoraban errores en silencio.
"""
import logging
import os
import platform
import sqlite3
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .version import NOMBRE, VERSION

_logger = None


def carpeta_datos() -> Path:
    """Carpeta de datos del usuario (~/.textilflow); se puede cambiar con la variable TEXTILFLOW_HOME."""
    return Path(os.environ.get("TEXTILFLOW_HOME") or (Path.home() / ".textilflow"))


def ruta_log() -> Path:
    return carpeta_datos() / "textilflow.log"


def _log() -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = logging.getLogger("textilflow")
        _logger.setLevel(logging.INFO)
        _logger.propagate = False
        try:
            ruta_log().parent.mkdir(parents=True, exist_ok=True)
            h = RotatingFileHandler(ruta_log(), maxBytes=512_000, backupCount=2, encoding="utf-8")
            h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            _logger.addHandler(h)
        except OSError:
            _logger.addHandler(logging.NullHandler())      # sin permisos de escritura: no se registra, pero no se rompe nada
    return _logger


def info(texto: str) -> None:
    _log().info(texto)


def registrar(contexto: str, exc: BaseException | None = None) -> None:
    """Guarda en el log un error que se maneja en silencio, indicando dónde ocurrió."""
    if exc is None:
        _log().error(contexto)
    else:
        _log().error("%s: %s", contexto, "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))


def _donde(tb) -> str:
    """Último punto del propio programa por donde pasó el error: «archivo · función (línea N)»."""
    marcos = [f for f in traceback.extract_tb(tb) if "textilflow" in f.filename.replace("\\", "/")]
    f = marcos[-1] if marcos else (traceback.extract_tb(tb)[-1] if tb else None)
    if f is None:
        return "no se pudo determinar"
    nombre = Path(f.filename).name
    return f"{nombre} · {f.name} (línea {f.lineno})"


def describir(tipo, exc, tb) -> dict:
    """Convierte una excepción en: título, qué pasó (claro), qué se puede hacer, dónde, detalle técnico."""
    msg = str(exc)
    sugerencia = "Puede continuar trabajando. Si el problema se repite, envíe el detalle técnico de abajo."
    if isinstance(exc, sqlite3.OperationalError) and "locked" in msg.lower():
        titulo, que = "La base de datos está en uso", ("Otro programa o ventana de TextilFlow tiene abierto el archivo de datos "
                                                      "y no permite guardar en este momento.")
        sugerencia = "Cierre la otra ventana de TextilFlow e inténtelo de nuevo."
    elif isinstance(exc, sqlite3.OperationalError) and ("readonly" in msg.lower() or "read-only" in msg.lower()):
        titulo, que = "No se puede guardar", "El archivo de datos es de solo lectura o está en una carpeta sin permisos."
        sugerencia = "Revise los permisos de la carpeta ~/.textilflow o abra el programa con otra ruta (--db)."
    elif isinstance(exc, sqlite3.OperationalError) and "full" in msg.lower():
        titulo, que = "Disco lleno", "No hay espacio en el disco para guardar los datos."
        sugerencia = "Libere espacio y vuelva a intentarlo."
    elif isinstance(exc, sqlite3.IntegrityError):
        titulo, que = "Dato repetido o relacionado", ("Se intentó guardar un dato que choca con otro ya existente "
                                                      "o que todavía está siendo usado en otra parte (por ejemplo, un área con rutas).")
        sugerencia = "Revise que el código no esté repetido o elimine primero lo que depende de ese registro."
    elif isinstance(exc, sqlite3.Error):
        titulo, que = "Error en la base de datos", "La base de datos devolvió un error al leer o guardar."
    elif isinstance(exc, PermissionError):
        titulo, que = "Sin permiso para el archivo", "Windows no permitió leer o escribir un archivo (¿está abierto en Excel?)."
        sugerencia = "Cierre el archivo en el otro programa o elija otra carpeta."
    elif isinstance(exc, FileNotFoundError):
        titulo, que = "No se encontró un archivo", f"El programa buscó un archivo que no existe: {exc.filename or msg}"
    elif isinstance(exc, MemoryError):
        titulo, que = "Memoria insuficiente", "La operación necesita más memoria de la disponible."
        sugerencia = "Reduzca el número de réplicas, la demanda (%) o los pedidos e intente de nuevo."
    elif isinstance(exc, ZeroDivisionError):
        titulo, que = "Cálculo imposible", "Una fórmula intentó dividir por cero; suele pasar con tiempos, capacidades o velocidades en 0."
        sugerencia = "Revise que velocidad, capacidad y tiempos de las áreas y del escenario sean mayores que 0."
    elif isinstance(exc, (KeyError, IndexError, AttributeError, TypeError)):
        titulo, que = "Error interno del programa", ("Faltó un dato que el programa esperaba encontrar "
                                                     "(puede pasar con datos incompletos o inconsistentes).")
    elif isinstance(exc, ValueError):
        titulo, que = "Valor no válido", "Se recibió un valor que no se pudo interpretar."
    else:
        titulo, que = "Ocurrió un error inesperado", "El programa encontró una situación que no esperaba."
    detalle = "".join(traceback.format_exception(tipo, exc, tb))
    return {"titulo": titulo, "que": que, "sugerencia": sugerencia, "donde": _donde(tb),
            "resumen": f"{tipo.__name__}: {msg}", "detalle": detalle}


def informe_texto(d: dict) -> str:
    """Texto listo para copiar y pegar al reportar el error."""
    return (f"{NOMBRE} v{VERSION} · {platform.platform()} · Python {platform.python_version()}\n"
            f"{d['titulo']}\nQué pasó: {d['que']}\nDónde: {d['donde']}\nTécnico: {d['resumen']}\n\n{d['detalle']}")
