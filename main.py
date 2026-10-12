import tkinter as tk
from tkinter import ttk

import database
from views.dashboard import DashboardTab
from views.datos import DatosTab
from views.resultados import ResultadosTab


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


if __name__ == "__main__":
    database.inicializar()
    App().mainloop()