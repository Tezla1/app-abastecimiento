from tkinter import ttk


class DatosTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Ingresar datos (pendiente)").pack(pady=20)