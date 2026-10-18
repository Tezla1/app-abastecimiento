"""Exportación de resultados a archivos (sin interfaz)."""
import csv
import re
from datetime import datetime

COLUMNAS = (
    "empresa", "escenario_base", "escenario_alternativo", "indicador",
    "valor_base", "valor_alternativo", "variacion_pct", "fecha_exportacion",
)


def _numero(valor):
    """Número con 2 decimales y coma decimal (Excel en español); vacío si no hay dato."""
    return "" if valor is None else f"{valor:.2f}".replace(".", ",")


def nombre_archivo_seguro(texto):
    """Convierte un texto en un nombre de archivo válido en Windows."""
    limpio = re.sub(r'[<>:"/\\|?*\s]+', "_", texto).strip("._")
    return limpio or "resultados"


def exportar_comparacion_csv(ruta, empresa, base, alt, filas, fecha=None):
    """Escribe la tabla de comparación en un CSV (UTF-8 con BOM, separador ';').

    empresa, base y alt son nombres (alt puede ser None si no se comparó).
    filas es la lista 'filas' que devuelve analisis.comparar_escenarios.
    """
    fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(COLUMNAS)
        for f in filas:
            escritor.writerow([
                empresa, base, alt or "", f["indicador"],
                _numero(f["base"]), _numero(f["alternativo"]),
                _numero(f["variacion_pct"]), fecha,
            ])