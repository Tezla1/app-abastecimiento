from tkinter import ttk

from views.formato import SIN_DATOS, fmt, fmt_variacion

FUENTE_VALOR = ("Helvetica", 18, "bold")

INDICADORES = (
    ("tiempo_abastecimiento_prom", "Tiempo promedio (min)"),
    ("distancia_total", "Distancia total (m)"),
    ("espera_prom", "Espera promedio (min)"),
    ("utilizacion_pct", "Utilización (%)"),
    ("solicitudes_atendidas_pct", "Solicitudes atendidas (%)"),
)


class TarjetasResumen(ttk.Frame):
    """Tarjetas con el resumen de la empresa y los indicadores. No calcula nada."""

    def __init__(self, parent):
        super().__init__(parent)
        for columna in range(5):
            self.columnconfigure(columna, weight=1, uniform="tarjeta")

        self.v_empresa, _ = self._tarjeta(0, 0, "Empresa activa", ancho=3)
        self.v_escenarios, _ = self._tarjeta(0, 3, "Escenarios")
        self.v_registros, _ = self._tarjeta(0, 4, "Registros")

        self._indicadores = {}
        for columna, (clave, titulo) in enumerate(INDICADORES):
            self._indicadores[clave] = self._tarjeta(1, columna, titulo)

        ttk.Label(
            self,
            text="Cada tarjeta muestra el valor del escenario base; la segunda línea, "
                 "el del escenario alternativo y su variación.",
        ).grid(row=2, column=0, columnspan=5, sticky="w", padx=4, pady=(0, 4))

    def _tarjeta(self, fila, columna, titulo, ancho=1):
        marco = ttk.LabelFrame(self, text=titulo)
        marco.grid(row=fila, column=columna, columnspan=ancho, sticky="nsew", padx=4, pady=4)
        valor = ttk.Label(marco, text=SIN_DATOS, font=FUENTE_VALOR)
        valor.pack(padx=8, pady=(4, 0))
        detalle = ttk.Label(marco, text="")
        detalle.pack(padx=8, pady=(0, 4))
        return valor, detalle

    def mostrar(self, empresa, n_escenarios, n_registros, filas=None, hay_alt=False):
        """filas: lista de dicts de analisis.comparar_escenarios (None = sin indicadores)."""
        self.v_empresa.config(text=empresa or SIN_DATOS)
        self.v_escenarios.config(text=str(n_escenarios))
        self.v_registros.config(text=str(n_registros))

        por_clave = {f["clave"]: f for f in (filas or [])}
        for clave, (valor, detalle) in self._indicadores.items():
            fila = por_clave.get(clave)
            valor.config(text=fmt(fila["base"]) if fila else SIN_DATOS)
            if fila and hay_alt:
                detalle.config(
                    text=f'Alt.: {fmt(fila["alternativo"])}  ({fmt_variacion(fila["variacion_pct"])})')
            else:
                detalle.config(text="")