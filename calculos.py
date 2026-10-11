import pandas as pd

ETIQUETAS = {
    "tiempo_abastecimiento_prom": "Tiempo promedio de abastecimiento (min)",
    "distancia_total": "Distancia total (m)",
    "distancia_prom": "Distancia promedio por solicitud (m)",
    "espera_prom": "Tiempo promedio de espera (min)",
    "utilizacion_pct": "Utilización del recurso (%)",
    "solicitudes_atendidas_pct": "Solicitudes atendidas (%)",
}

# Sin estos indicadores no tiene sentido comparar dos escenarios
CLAVES_REQUERIDAS = (
    "tiempo_abastecimiento_prom",
    "distancia_total",
    "espera_prom",
    "solicitudes_atendidas_pct",
)


def calcular_indicadores(escenario, registros):
    """Calcula los indicadores de un escenario.

    escenario: dict con num_recursos y tiempo_observacion_min.
    registros: lista de dicts (filas de la tabla registro).
    Devuelve un dict; un indicador es None si no hay datos suficientes.
    """
    ind = {clave: None for clave in ETIQUETAS}
    ind["n_registros"] = len(registros)
    ind["n_atendidas"] = 0

    if not registros:
        return ind

    df = pd.DataFrame(registros)
    atendidas = df[df["atendida"].astype(int) == 1]
    ind["n_atendidas"] = len(atendidas)
    ind["solicitudes_atendidas_pct"] = len(atendidas) / len(df) * 100

    if atendidas.empty:
        return ind

    ciclo = atendidas["tiempo_espera_min"] + atendidas["tiempo_recorrido_min"]
    ind["tiempo_abastecimiento_prom"] = float(ciclo.mean())
    ind["distancia_total"] = float(atendidas["distancia_m"].sum())
    ind["distancia_prom"] = float(atendidas["distancia_m"].mean())
    ind["espera_prom"] = float(atendidas["tiempo_espera_min"].mean())

    t_obs = escenario.get("tiempo_observacion_min")
    n_recursos = escenario.get("num_recursos") or 1
    if t_obs:
        ocupado = float(atendidas["tiempo_recorrido_min"].sum())
        ind["utilizacion_pct"] = ocupado / (t_obs * n_recursos) * 100

    return ind


def variacion_pct(base, alternativo):
    """V = ((Xalt - Xbase) / Xbase) * 100. None si no se puede calcular."""
    if base is None or alternativo is None or base == 0:
        return None
    return (alternativo - base) / base * 100


def verificar_comparable(ind_base, ind_alt):
    """Devuelve (es_comparable, lista_de_problemas)."""
    problemas = []
    for nombre, ind in (("base", ind_base), ("alternativo", ind_alt)):
        faltan = [ETIQUETAS[k] for k in CLAVES_REQUERIDAS if ind.get(k) is None]
        if faltan:
            problemas.append(
                f"El escenario {nombre} no tiene datos suficientes para: {', '.join(faltan)}."
            )
    return (len(problemas) == 0, problemas)


def comparar(ind_base, ind_alt):
    """Tabla de comparación: una fila por indicador con su variación porcentual."""
    return [
        {
            "clave": clave,
            "indicador": etiqueta,
            "base": ind_base.get(clave),
            "alternativo": ind_alt.get(clave),
            "variacion_pct": variacion_pct(ind_base.get(clave), ind_alt.get(clave)),
        }
        for clave, etiqueta in ETIQUETAS.items()
    ]