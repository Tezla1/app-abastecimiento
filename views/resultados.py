from tkinter import filedialog, messagebox, ttk

import analisis
import exportacion
from views.selector_escenarios import SelectorEscenarios
from views.tabla_comparacion import TablaComparacion


class ResultadosTab(ttk.Frame):
    """Pestaña 'Resultados': conecta el selector, el análisis y la tabla."""

    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._ultimo = None  # contexto de la última comparación mostrada, para exportarla

        self.tabla = TablaComparacion(self)
        self.selector = SelectorEscenarios(self, on_cambio=self._calcular)
        self.selector.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.tabla.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        ttk.Button(self, text="Exportar tabla a CSV…", command=self._exportar_csv).grid(
            row=2, column=0, sticky="e", padx=8, pady=(0, 8))

        self.actualizar()

    def actualizar(self):
        """Se llama al abrir la pestaña."""
        self.selector.actualizar()

    def _calcular(self):
        base, alt = self.selector.seleccion()
        if base is None:
            self._ultimo = None
            self.tabla.mostrar(
                [], avisos=["Selecciona una empresa que tenga al menos un escenario."])
            return

        r = analisis.comparar_escenarios(base, alt)
        hay_alt = r["ind_alt"] is not None
        self._ultimo = {
            "empresa": self.selector.empresa()["nombre"],
            "base": base["nombre"],
            "alt": alt["nombre"] if hay_alt else None,
            "filas": r["filas"],
        }
        self.tabla.mostrar(r["filas"], self._resumen(r["ind_base"], r["ind_alt"]), r["avisos"])

    def _exportar_csv(self):
        if self._ultimo is None:
            messagebox.showwarning("Sin resultados", "No hay resultados para exportar.")
            return
        u = self._ultimo
        sugerido = f'comparacion_{u["empresa"]}_{u["base"]}'
        if u["alt"]:
            sugerido += f'_vs_{u["alt"]}'
        ruta = filedialog.asksaveasfilename(
            title="Exportar tabla de comparación", defaultextension=".csv",
            initialfile=exportacion.nombre_archivo_seguro(sugerido) + ".csv",
            filetypes=[("Archivos CSV", "*.csv")])
        if not ruta:  # el usuario canceló
            return
        try:
            exportacion.exportar_comparacion_csv(
                ruta, u["empresa"], u["base"], u["alt"], u["filas"])
        except OSError:
            messagebox.showerror(
                "No se pudo guardar",
                "No se pudo guardar el archivo. Si está abierto en otro programa "
                "(por ejemplo, Excel), ciérralo e inténtalo de nuevo.")
            return
        messagebox.showinfo("Exportación completa", f"Tabla guardada en:\n{ruta}")

    @staticmethod
    def _resumen(ind_base, ind_alt):
        texto = (f'Base: {ind_base["n_registros"]} registros '
                 f'({ind_base["n_atendidas"]} atendidos)')
        if ind_alt is not None:
            texto += (f'   |   Alternativo: {ind_alt["n_registros"]} registros '
                      f'({ind_alt["n_atendidas"]} atendidos)')
        return texto