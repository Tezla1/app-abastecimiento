from tkinter import ttk

import analisis
from views.selector_escenarios import SelectorEscenarios
from views.tabla_comparacion import TablaComparacion


class ResultadosTab(ttk.Frame):
    """Pestaña 'Resultados': conecta el selector, el análisis y la tabla."""

    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.tabla = TablaComparacion(self)
        self.selector = SelectorEscenarios(self, on_cambio=self._calcular)
        self.selector.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.tabla.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.actualizar()

    def actualizar(self):
        """Se llama al abrir la pestaña."""
        self.selector.actualizar()

    def _calcular(self):
        base, alt = self.selector.seleccion()
        if base is None:
            self.tabla.mostrar(
                [], avisos=["Selecciona una empresa que tenga al menos un escenario."])
            return
        r = analisis.comparar_escenarios(base, alt)
        self.tabla.mostrar(r["filas"], self._resumen(r["ind_base"], r["ind_alt"]), r["avisos"])

    @staticmethod
    def _resumen(ind_base, ind_alt):
        texto = (f'Base: {ind_base["n_registros"]} registros '
                 f'({ind_base["n_atendidas"]} atendidos)')
        if ind_alt is not None:
            texto += (f'   |   Alternativo: {ind_alt["n_registros"]} registros '
                      f'({ind_alt["n_atendidas"]} atendidos)')
        return texto