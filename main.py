import tkinter as tk
import database
from tkinter import ttk

from views.dashboard import DashboardTab
from views.datos import DatosTab
from views.resultados import ResultadosTab


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Análisis de abastecimiento interno - Talleres textiles de Soacha")
        self.geometry("1150x720")
        self.minsize(800, 500)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        notebook.add(DashboardTab(notebook), text="Dashboard")
        notebook.add(DatosTab(notebook), text="Ingresar datos")
        notebook.add(ResultadosTab(notebook), text="Resultados")


if __name__ == "__main__":
    database.inicializar()
    App().mainloop()