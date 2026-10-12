SIN_DATOS = "—"


def fmt(valor):
    """Número con 2 decimales, o '—' si no hay dato."""
    return SIN_DATOS if valor is None else f"{valor:.2f}"


def fmt_variacion(valor):
    """Variación porcentual con signo, o '—' si no se pudo calcular."""
    return SIN_DATOS if valor is None else f"{valor:+.2f} %"