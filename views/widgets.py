import tkinter as tk
from tkinter import ttk


def campo(parent, fila, etiqueta, valor_inicial=""):
    """Etiqueta + Entry en una fila de grid. Devuelve la StringVar del Entry."""
    ttk.Label(parent, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=4, pady=2)
    var = tk.StringVar(value=valor_inicial)
    ttk.Entry(parent, textvariable=var, width=22).grid(
        row=fila, column=1, sticky="ew", padx=4, pady=2)
    return var