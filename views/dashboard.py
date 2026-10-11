from tkinter import ttk


class DashboardTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Dashboard (pendiente)").pack(pady=20)