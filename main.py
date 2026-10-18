import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import database
from views.dashboard import DashboardTab
from views.datos import DatosTab
from views.resultados import ResultadosTab

RUTA_LOG = Path(__file__).parent / "data" / "errores.log"


def configurar_log():
    RUTA_LOG.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=RUTA_LOG, level=logging.ERROR, encoding="utf-8",
        format="%(asctime)s %(levelname)s %(message)s")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Análisis de abastecimiento interno - Talleres textiles de Soacha")
        self.geometry("1150x720")
        self.minsize(800, 500)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.notebook.add(DashboardTab(self.notebook), text="Dashboard")
        self.notebook.add(DatosTab(self.notebook), text="Ingresar datos")
        self.notebook.add(ResultadosTab(self.notebook), text="Resultados")
        self.notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)

    def _al_cambiar_pestana(self, evento):
        """Cada pestaña que tenga un método actualizar() se refresca al abrirse."""
        pestana = self.nametowidget(self.notebook.select())
        if hasattr(pestana, "actualizar"):
            pestana.actualizar()

    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        """Errores inesperados de la interfaz: se registran y se avisa sin cerrar la app."""
        logging.error("Error inesperado en la interfaz",
                      exc_info=(exc_type, exc_value, exc_traceback))
        messagebox.showerror(
            "Error inesperado",
            "Ocurrió un error inesperado, pero la aplicación sigue abierta.\n"
            f"Detalle: {exc_type.__name__}: {exc_value}\n\n"
            "El error quedó registrado en data/errores.log.")


def _error_fatal(mensaje):
    raiz = tk.Tk()
    raiz.withdraw()
    messagebox.showerror("No se pudo iniciar la aplicación", mensaje)
    raiz.destroy()


if __name__ == "__main__":
    configurar_log()
    try:
        database.inicializar()
    except Exception as error:
        logging.exception("No se pudo inicializar la base de datos")
        _error_fatal(f"No se pudo abrir la base de datos.\n\nDetalle: {error}")
        raise SystemExit(1)
    App().mainloop()