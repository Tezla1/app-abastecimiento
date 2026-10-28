# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Fórmulas y textos fijos que se muestran en las pantallas del modelo matemático y la comparación.

FORMULAS = {
    "tiempo_abastecimiento_prom": "media(espera + recorrido) de los traslados atendidos",
    "distancia_total": "Σ distancia_m de los traslados atendidos",
    "distancia_prom": "media(distancia_m) de los traslados atendidos",
    "espera_prom": "media(tiempo de espera) de los traslados atendidos",
    "utilizacion_pct": "Σ tiempo de recorrido / (T observación × N recursos) × 100",
    "solicitudes_atendidas_pct": "atendidos / total de traslados × 100",
}

FORMULA_VARIACION = "V = ((Xalt − Xbase) / Xbase) × 100"

MEJOR_SI_BAJA = {
    "tiempo_abastecimiento_prom": True,
    "distancia_total": True,
    "distancia_prom": True,
    "espera_prom": True,
    "utilizacion_pct": None,
    "solicitudes_atendidas_pct": False,
}

DECIMALES = {
    "tiempo_abastecimiento_prom": 2, "distancia_total": 1, "distancia_prom": 1,
    "espera_prom": 2, "utilizacion_pct": 1, "solicitudes_atendidas_pct": 1,
}
