import csv
import io

import validaciones

COLUMNAS = (
    "origen", "destino", "distancia_m", "carga_kg",
    "tiempo_espera_min", "tiempo_recorrido_min", "atendida",
)


def _leer_texto(ruta):
    """Lee el archivo probando las codificaciones habituales (UTF-8 y Windows)."""
    with open(ruta, "rb") as archivo:
        contenido = archivo.read()
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            return contenido.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return contenido.decode("latin-1")


def _detectar_separador(texto):
    """Elige entre ';' (Excel en español), ',' y tabulador según la primera línea."""
    primera_linea = texto.splitlines()[0]
    return max((";", ",", "\t"), key=primera_linea.count)


def leer_registros_csv(ruta):
    """Lee y valida un CSV de registros. Devuelve (registros, errores).

    Es 'todo o nada': si hay algún error, la lista de registros queda vacía y no se
    debe importar nada. Los registros válidos tienen las claves que espera
    database.crear_registros.
    """
    try:
        texto = _leer_texto(ruta).lstrip("\r\n")
    except OSError:
        return [], ["No se pudo abrir el archivo. Verifica la ruta y que no esté "
                    "abierto en otro programa."]
    if not texto.strip():
        return [], ["El archivo está vacío."]

    lector = csv.DictReader(
        io.StringIO(texto, newline=""), delimiter=_detectar_separador(texto))
    lector.fieldnames = [(c or "").strip().lower() for c in (lector.fieldnames or [])]

    faltan = [c for c in COLUMNAS if c not in lector.fieldnames]
    if faltan:
        return [], [f"Faltan columnas obligatorias: {', '.join(faltan)}."]

    registros, errores = [], []
    for fila in lector:
        if all(not (valor or "").strip()
               for clave, valor in fila.items() if clave is not None):
            continue  # fila vacía

        atendida, error_atendida = validaciones.a_booleano(fila["atendida"], "Atendida")
        datos, errores_fila = validaciones.validar_registro(
            fila["origen"], fila["destino"], fila["distancia_m"], fila["carga_kg"],
            fila["tiempo_espera_min"], fila["tiempo_recorrido_min"], bool(atendida))
        if error_atendida:
            errores_fila = errores_fila + [error_atendida]

        if errores_fila:
            errores.extend(f"Fila {lector.line_num}: {e}" for e in errores_fila)
        else:
            registros.append(datos)

    if errores:
        return [], errores
    if not registros:
        return [], ["El archivo no contiene registros."]
    return registros, []