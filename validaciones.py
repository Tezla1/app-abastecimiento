import math
import unicodedata

TIPOS_ESCENARIO = ("Base", "Recurso móvil")


def a_numero(texto, campo, entero=False, minimo=0.0, estricto=False, obligatorio=True):
    """Convierte el texto de un formulario en número. Devuelve (valor, error)."""
    if texto is None or str(texto).strip() == "":
        if obligatorio:
            return None, f"{campo}: campo obligatorio."
        return None, None
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        return None, f"{campo}: debe ser un número."
    if not math.isfinite(valor):
        return None, f"{campo}: debe ser un número."
    if entero and valor != int(valor):
        return None, f"{campo}: debe ser un número entero."
    if estricto and valor <= minimo:
        return None, f"{campo}: debe ser mayor que {minimo:g}."
    if not estricto and valor < minimo:
        if minimo == 0:
            return None, f"{campo}: no puede ser negativo."
        return None, f"{campo}: debe ser mayor o igual a {minimo:g}."
    return (int(valor) if entero else valor), None

_VERDADEROS = {"si", "s", "1", "true", "verdadero", "yes", "y"}
_FALSOS = {"no", "n", "0", "false", "falso"}


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def a_booleano(texto, campo):
    """Convierte Sí/No, 1/0 o true/false en booleano. Devuelve (valor, error)."""
    if texto is None or str(texto).strip() == "":
        return None, f"{campo}: campo obligatorio."
    clave = _sin_tildes(str(texto).strip().lower())
    if clave in _VERDADEROS:
        return True, None
    if clave in _FALSOS:
        return False, None
    return None, f"{campo}: debe ser Sí/No, 1/0 o true/false."


def _tomar(errores, resultado):
    """Guarda el error (si hay) y devuelve el valor convertido."""
    valor, error = resultado
    if error:
        errores.append(error)
    return valor


def _texto_obligatorio(errores, texto, campo):
    texto = (texto or "").strip()
    if not texto:
        errores.append(f"{campo}: campo obligatorio.")
    return texto


def validar_empresa(nombre, area_m2="", num_estaciones="", num_operarios=""):
    errores = []
    datos = {
        "nombre": _texto_obligatorio(errores, nombre, "Nombre de la empresa"),
        "area_m2": _tomar(errores, a_numero(area_m2, "Área (m²)", obligatorio=False)),
        "num_estaciones": _tomar(errores, a_numero(
            num_estaciones, "N.º de estaciones", entero=True, obligatorio=False)),
        "num_operarios": _tomar(errores, a_numero(
            num_operarios, "N.º de operarios", entero=True, obligatorio=False)),
    }
    return (None if errores else datos), errores


def validar_escenario(nombre, tipo, num_recursos, capacidad_kg="", velocidad_m_min="",
                      obstaculos=False, tiempo_observacion_min=""):
    errores = []
    nombre = _texto_obligatorio(errores, nombre, "Nombre del escenario")
    if tipo not in TIPOS_ESCENARIO:
        errores.append("Tipo de escenario: debe ser Base o Recurso móvil.")
    datos = {
        "nombre": nombre,
        "tipo": tipo,
        "num_recursos": _tomar(errores, a_numero(
            num_recursos, "N.º de recursos", entero=True, minimo=1)),
        "capacidad_kg": _tomar(errores, a_numero(
            capacidad_kg, "Capacidad (kg)", obligatorio=False)),
        "velocidad_m_min": _tomar(errores, a_numero(
            velocidad_m_min, "Velocidad (m/min)", obligatorio=False)),
        "obstaculos": bool(obstaculos),
        "tiempo_observacion_min": _tomar(errores, a_numero(
            tiempo_observacion_min, "Tiempo de observación (min)",
            estricto=True, obligatorio=False)),
    }
    return (None if errores else datos), errores


def validar_registro(origen, destino, distancia_m, carga_kg,
                     tiempo_espera_min, tiempo_recorrido_min, atendida):
    errores = []
    datos = {
        "origen": _texto_obligatorio(errores, origen, "Origen"),
        "destino": _texto_obligatorio(errores, destino, "Destino"),
        "distancia_m": _tomar(errores, a_numero(distancia_m, "Distancia (m)")),
        "carga_kg": _tomar(errores, a_numero(carga_kg, "Carga (kg)")),
        "tiempo_espera_min": _tomar(errores, a_numero(
            tiempo_espera_min, "Tiempo de espera (min)")),
        "tiempo_recorrido_min": _tomar(errores, a_numero(
            tiempo_recorrido_min, "Tiempo de recorrido (min)")),
        "atendida": bool(atendida),
    }
    return (None if errores else datos), errores