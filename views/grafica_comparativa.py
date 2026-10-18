from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from views.formato import INDICADORES, fmt

COLOR_BASE = "#4C72B0"
COLOR_ALT = "#DD8452"


class GraficaComparativa(ttk.LabelFrame):
    """Barras Base vs Alternativo: un mini-gráfico por indicador, cada uno con su escala."""

    def __init__(self, parent):
        super().__init__(parent, text="Comparación de indicadores")
        self._hay_grafica = False
        ttk.Button(self, text="Guardar gráfica como PNG…", command=self._guardar_png).pack(
            side="bottom", anchor="e", padx=4, pady=(0, 4))
        self.figura = Figure(figsize=(10, 3.6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figura, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        self.mostrar_mensaje("Sin datos para graficar.")

    def mostrar_mensaje(self, texto):
        self._hay_grafica = False
        self.figura.clear()
        self.figura.text(0.5, 0.5, texto, ha="center", va="center")
        self.canvas.draw_idle()

    def mostrar(self, filas, nombre_base, nombre_alt=None):
        """filas: lista de dicts de analisis.comparar_escenarios.
        nombre_alt=None significa que no se está comparando (solo se dibuja el base)."""
        por_clave = {f["clave"]: f for f in filas}
        datos = [(titulo, por_clave[clave]) for clave, titulo in INDICADORES
                 if clave in por_clave and por_clave[clave]["base"] is not None]
        if not datos:
            self.mostrar_mensaje("El escenario base no tiene datos suficientes para graficar.")
            return

        self.figura.clear()
        ejes = self.figura.subplots(1, len(datos), squeeze=False)[0]
        hay_barra_alt = False

        for eje, (titulo, fila) in zip(ejes, datos):
            valores, colores = [fila["base"]], [COLOR_BASE]
            if nombre_alt is not None and fila["alternativo"] is not None:
                valores.append(fila["alternativo"])
                colores.append(COLOR_ALT)
                hay_barra_alt = True

            barras = eje.bar(range(len(valores)), valores, color=colores, width=0.6)
            eje.bar_label(barras, labels=[fmt(v) for v in valores], fontsize=9, padding=2)
            eje.set_xticks(range(len(valores)))
            eje.set_xticklabels(["Base", "Alt."][:len(valores)], fontsize=9)
            eje.set_title(titulo.replace(" (", "\n("), fontsize=9)
            eje.set_ylim(0, max(valores) * 1.2 if max(valores) > 0 else 1)
            eje.tick_params(axis="y", labelsize=8)
            eje.spines[["top", "right"]].set_visible(False)

        manejadores = [Patch(color=COLOR_BASE, label=f"Base: {nombre_base}")]
        if hay_barra_alt:
            manejadores.append(Patch(color=COLOR_ALT, label=f"Alternativo: {nombre_alt}"))
        self.figura.legend(handles=manejadores, loc="lower center", ncol=2,
                           frameon=False, fontsize=9)
        self.figura.subplots_adjust(left=0.05, right=0.98, top=0.82, bottom=0.2, wspace=0.35)
        self.canvas.draw_idle()
        self._hay_grafica = True

    def _guardar_png(self):
        if not self._hay_grafica:
            messagebox.showwarning("Sin gráfica", "No hay una gráfica para guardar.")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar gráfica", defaultextension=".png",
            initialfile="grafica_comparativa.png",
            filetypes=[("Imagen PNG", "*.png")])
        if not ruta:  # el usuario canceló
            return
        try:
            self.figura.savefig(ruta, dpi=200, facecolor="white")
        except OSError:
            messagebox.showerror(
                "No se pudo guardar",
                "No se pudo guardar la imagen. Si hay un archivo con ese nombre abierto "
                "en otro programa, ciérralo e inténtalo de nuevo.")
            return
        messagebox.showinfo("Gráfica guardada", f"Imagen guardada en:\n{ruta}")