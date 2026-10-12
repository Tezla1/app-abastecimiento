from tkinter import ttk

import analisis
import database
from views.selector_escenarios import SelectorEscenarios
from views.tarjetas_resumen import TarjetasResumen


class DashboardTab(ttk.Frame):
    """Pestaña 'Dashboard': resumen de la empresa y de la comparación. No captura datos."""

    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)  # aquí irá la gráfica (paso 6b)

        self.tarjetas = TarjetasResumen(self)
        self.selector = SelectorEscenarios(self, on_cambio=self._refrescar)
        self.selector.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.tarjetas.grid(row=1, column=0, sticky="ew", padx=8)

        self.actualizar()

    def actualizar(self):
        """Se llama al abrir la pestaña."""
        self.selector.actualizar()

    def _refrescar(self):
        empresa = self.selector.empresa()
        if empresa is None:
            self.tarjetas.mostrar(None, 0, 0)
            return

        n_escenarios = len(database.listar_escenarios(empresa["id"]))
        n_registros = database.contar_registros_empresa(empresa["id"])
        base, alt = self.selector.seleccion()
        if base is None:
            self.tarjetas.mostrar(empresa["nombre"], n_escenarios, n_registros)
            return

        r = analisis.comparar_escenarios(base, alt)
        self.tarjetas.mostrar(
            empresa["nombre"], n_escenarios, n_registros, r["filas"], hay_alt=alt is not None)