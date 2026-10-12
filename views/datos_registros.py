import tkinter as tk
from tkinter import messagebox, ttk

import database
import validaciones
from views.widgets import campo

MENSAJE_SIN_ESCENARIO = "Selecciona un escenario en la tabla de la izquierda."


class PanelRegistros(ttk.LabelFrame):
    """Formulario y tabla de registros experimentales del escenario seleccionado."""

    def __init__(self, parent, on_cambio):
        super().__init__(parent, text="Registros experimentales")
        self.on_cambio = on_cambio
        self.escenario_id = None
        self.escenario_nombre = None
        self.columnconfigure(1, weight=1)

        self.lbl_escenario = ttk.Label(self, text=MENSAJE_SIN_ESCENARIO)
        self.lbl_escenario.grid(row=0, column=0, columnspan=3, sticky="w", padx=4, pady=(4, 8))

        self.v_origen = campo(self, 1, "Origen")
        self.v_destino = campo(self, 2, "Destino")
        self.v_distancia = campo(self, 3, "Distancia (m)")
        self.v_carga = campo(self, 4, "Carga (kg)")
        self.v_espera = campo(self, 5, "Tiempo de espera (min)")
        self.v_recorrido = campo(self, 6, "Tiempo de recorrido (min)")
        self.v_atendida = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text="Solicitud atendida", variable=self.v_atendida).grid(
            row=7, column=1, sticky="w", padx=4)
        ttk.Button(self, text="Agregar registro", command=self._agregar).grid(
            row=8, column=1, sticky="e", padx=4, pady=4)

        columnas = (("origen", "Origen", 80), ("destino", "Destino", 80),
                    ("distancia", "Dist. (m)", 55), ("carga", "Carga", 55),
                    ("espera", "Espera", 55), ("recorrido", "Recorr.", 60),
                    ("atendida", "Atend.", 55))
        self.tabla = ttk.Treeview(
            self, columns=[c[0] for c in columnas], show="headings",
            height=8, selectmode="browse")
        for clave, texto, ancho in columnas:
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, anchor="w")
        barra = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=(4, 0), pady=4)
        barra.grid(row=9, column=2, sticky="ns", pady=4)
        self.rowconfigure(9, weight=1)
        ttk.Button(self, text="Eliminar registro seleccionado", command=self._eliminar).grid(
            row=10, column=1, sticky="e", padx=4, pady=(0, 4))

    def mostrar_escenario(self, escenario_id, nombre):
        """Muestra los registros del escenario indicado (None = panel vacío)."""
        self.escenario_id = escenario_id
        self.escenario_nombre = nombre
        self._recargar()

    def _recargar(self):
        self.tabla.delete(*self.tabla.get_children())
        if self.escenario_id is None:
            self.lbl_escenario.config(text=MENSAJE_SIN_ESCENARIO)
            return
        registros = database.listar_registros(self.escenario_id)
        for r in registros:
            self.tabla.insert(
                "", "end", iid=str(r["id"]),
                values=(r["origen"], r["destino"], r["distancia_m"], r["carga_kg"],
                        r["tiempo_espera_min"], r["tiempo_recorrido_min"],
                        "Sí" if r["atendida"] else "No"))
        self.tabla.yview_moveto(1)  # baja hasta el último registro agregado
        self.lbl_escenario.config(
            text=f"Escenario: {self.escenario_nombre} — {len(registros)} registros")

    def _agregar(self):
        if self.escenario_id is None:
            messagebox.showwarning("Sin escenario", "Selecciona primero un escenario.")
            return
        datos, errores = validaciones.validar_registro(
            self.v_origen.get(), self.v_destino.get(), self.v_distancia.get(),
            self.v_carga.get(), self.v_espera.get(), self.v_recorrido.get(),
            self.v_atendida.get())
        if errores:
            messagebox.showerror("Datos no válidos", "\n".join(errores))
            return
        database.crear_registro(self.escenario_id, **datos)
        # Se conservan origen y destino para capturar varias filas seguidas más rápido
        for var in (self.v_distancia, self.v_carga, self.v_espera, self.v_recorrido):
            var.set("")
        self.v_atendida.set(True)
        self._recargar()
        self.on_cambio()

    def _eliminar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Selecciona un registro de la tabla.")
            return
        database.eliminar_registro(int(seleccion[0]))
        self._recargar()
        self.on_cambio()