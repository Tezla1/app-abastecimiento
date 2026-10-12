"""Capa de análisis: une la persistencia (database) y el cálculo (calculos) para las vistas."""
import calculos
import database


def _indicadores(escenario):
    registros = database.listar_registros(escenario["id"])
    return calculos.calcular_indicadores(escenario, registros)


def _avisos_utilizacion(ind_base, ind_alt):
    avisos = []
    for nombre, ind in (("base", ind_base), ("alternativo", ind_alt)):
        util = ind.get("utilizacion_pct") if ind else None
        if util is not None and util > 100:
            avisos.append(
                f"La utilización del escenario {nombre} supera el 100 %: revisa el "
                "tiempo de observación o el número de recursos.")
    return avisos


def comparar_escenarios(base, alt=None):
    """Calcula los indicadores del escenario base y, si se da alt, su comparación.

    Devuelve un dict con: ind_base, ind_alt (None si no hay alternativo),
    filas (una por indicador, para tablas y tarjetas), comparable (bool)
    y avisos (lista de textos).
    """
    ind_base = _indicadores(base)
    ind_alt = _indicadores(alt) if alt is not None else None

    avisos = []
    comparable = False
    if ind_alt is not None:
        comparable, problemas = calculos.verificar_comparable(ind_base, ind_alt)
        avisos += problemas

    filas = calculos.comparar(ind_base, ind_alt or {})
    if not comparable:  # regla del anteproyecto: no comparar sin datos suficientes
        for fila in filas:
            fila["variacion_pct"] = None

    avisos += _avisos_utilizacion(ind_base, ind_alt)
    return {
        "ind_base": ind_base,
        "ind_alt": ind_alt,
        "filas": filas,
        "comparable": comparable,
        "avisos": avisos,
    }