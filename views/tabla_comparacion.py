from tkinter import ttk

from views.formato import fmt, fmt_variacion

NOTA_VARIACION = (
    "Variación = (alternativo − base) / base × 100. En los indicadores que ya son "
    "porcentajes (utilización, solicitudes atendidas) es una variación relativa, "
    "no una diferencia en puntos porcentuales."
)


class TablaComparacion(ttk.LabelFrame):
    """Muestra la tabla de indicadores, el resumen y los avisos. No calcula nada."""

    def __init__(self, parent):
        super().__init__(parent, text="Indicadores")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        columnas = (("indicador", "Indicador", 330, "w"), ("base", "Escenario base", 150, "e"),
                    ("alt", "Escenario alternativo", 170, "e"), ("var", "Variación", 120, "e"))
        self.tabla = ttk.Treeview(
            self, columns=[c[0] for c in columnas], show="headings",
            height=7, selectmode="none")
        for clave, texto, ancho, ancla in columnas:
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, anchor=ancla)
        self.tabla.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.lbl_resumen = ttk.Label(self, text="")
        self.lbl_resumen.grid(row=1, column=0, sticky="w", padx=4)
        self.lbl_aviso = ttk.Label(self, text="", foreground="#b00020", wraplength=1000)
        self.lbl_aviso.grid(row=2, column=0, sticky="w", padx=4, pady=(4, 0))
        ttk.Label(self, text=NOTA_VARIACION, wraplength=1000).grid(
            row=3, column=0, sticky="w", padx=4, pady=4)

    def limpiar(self):
        self.tabla.delete(*self.tabla.get_children())
        self.lbl_resumen.config(text="")
        self.lbl_aviso.config(text="")

    def mostrar(self, filas, resumen="", avisos=()):
        """filas: lista de dicts con indicador, base, alternativo y variacion_pct."""
        self.limpiar()
        for f in filas:
            self.tabla.insert("", "end", values=(
                f["indicador"], fmt(f["base"]), fmt(f["alternativo"]),
                fmt_variacion(f["variacion_pct"])))
        self.lbl_resumen.config(text=resumen)
        self.lbl_aviso.config(text="\n".join(avisos))