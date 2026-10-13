from tkinter import ttk

import analisis
import database
from views.grafica_comparativa import GraficaComparativa
from views.selector_escenarios import SelectorEscenarios
from views.tarjetas_resumen import TarjetasResumen


class DashboardTab(ttk.Frame):
    """Pestaña 'Dashboard': resumen de la empresa y de la comparación. No captura datos."""

    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.tarjetas = TarjetasResumen(self)
        self.grafica = GraficaComparativa(self)
        self.selector = SelectorEscenarios(self, on_cambio=self._refrescar)
        self.selector.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.tarjetas.grid(row=1, column=0, sticky="ew", padx=8)
        self.grafica.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)

        self.actualizar()

    def actualizar(self):
        """Se llama al abrir la pestaña."""
        self.selector.actualizar()

    def _refrescar(self):
        empresa = self.selector.empresa()
        if empresa is None:
            self.tarjetas.mostrar(None, 0, 0)
            self.grafica.mostrar_mensaje("Crea una empresa y sus escenarios para ver la gráfica.")
            return

        n_escenarios = len(database.listar_escenarios(empresa["id"]))
        n_registros = database.contar_registros_empresa(empresa["id"])
        base, alt = self.selector.seleccion()
        if base is None:
            self.tarjetas.mostrar(empresa["nombre"], n_escenarios, n_registros)
            self.grafica.mostrar_mensaje("Esta empresa todavía no tiene escenarios.")
            return

        r = analisis.comparar_escenarios(base, alt)
        self.tarjetas.mostrar(
            empresa["nombre"], n_escenarios, n_registros, r["filas"], hay_alt=alt is not None)
        self.grafica.mostrar(r["filas"], base["nombre"], alt["nombre"] if alt else None)