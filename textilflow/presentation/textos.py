"""Textos del modelo matemático para mostrar en pantalla."""

FORMULAS = {
    "tiempo_abastecimiento_prom": "media(espera + recorrido) de las traslados atendidos",
    "distancia_total": "Σ distancia_m de las traslados atendidos",
    "distancia_prom": "media(distancia_m) de las traslados atendidos",
    "espera_prom": "media(tiempo de espera) de las traslados atendidos",
    "utilizacion_pct": "Σ tiempo de recorrido / (T observación × N recursos) × 100",
    "solicitudes_atendidas_pct": "atendidos / total de traslados × 100",
}

FORMULA_VARIACION = "V = ((Xalt − Xbase) / Xbase) × 100"

# Sentido de la mejora para colorear la variación (None = neutro, depende del contexto).
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
