import json
import os
import zipfile

from ...application.errors import ErrorDeNegocio
from ...application.ports import ProyectoArchive

NOMBRE_INTERNO = "proyecto.json"
LIMITE_BYTES = 200 * 1024 * 1024


class RlrArchive(ProyectoArchive):
    def escribir(self, ruta: str, datos: dict) -> None:
        tmp = f"{ruta}.tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(NOMBRE_INTERNO, json.dumps(datos, ensure_ascii=False, indent=1))
        os.replace(tmp, ruta)

    def leer(self, ruta: str) -> dict:
        try:
            with zipfile.ZipFile(ruta) as z:
                info = z.getinfo(NOMBRE_INTERNO)
                if info.file_size > LIMITE_BYTES:
                    raise ErrorDeNegocio("El respaldo es demasiado grande.")
                return json.loads(z.read(info).decode("utf-8"))
        except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError):
            raise ErrorDeNegocio("El archivo no es un respaldo .rlr válido.") from None
