from tkinter import ttk


class ResultadosTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Resultados (pendiente)").pack(pady=20)