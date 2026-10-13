SIN_DATOS = "—"

# Indicadores que muestran las tarjetas y la gráfica: (clave, título corto con unidad)
INDICADORES = (
    ("tiempo_abastecimiento_prom", "Tiempo promedio (min)"),
    ("distancia_total", "Distancia total (m)"),
    ("espera_prom", "Espera promedio (min)"),
    ("utilizacion_pct", "Utilización (%)"),
    ("solicitudes_atendidas_pct", "Solicitudes atendidas (%)"),
)


def fmt(valor):
    """Número con 2 decimales, o '—' si no hay dato."""
    return SIN_DATOS if valor is None else f"{valor:.2f}"


def fmt_variacion(valor):
    """Variación porcentual con signo, o '—' si no se pudo calcular."""
    return SIN_DATOS if valor is None else f"{valor:+.2f} %"