import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

import database
import validaciones
from views.widgets import campo


class PanelEscenarios(ttk.LabelFrame):
    """Formulario y tabla de escenarios de la empresa activa."""

    def __init__(self, parent, on_cambio):
        super().__init__(parent, text="Escenarios de la empresa activa")
        self.on_cambio = on_cambio
        self.empresa_id = None
        self.columnconfigure(1, weight=1)

        self.v_nombre = campo(self, 0, "Nombre")
        ttk.Label(self, text="Tipo").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        self.cmb_tipo = ttk.Combobox(self, values=validaciones.TIPOS_ESCENARIO, state="readonly")
        self.cmb_tipo.current(0)
        self.cmb_tipo.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        self.v_recursos = campo(self, 2, "N.º de recursos", "1")
        self.v_capacidad = campo(self, 3, "Capacidad (kg)")
        self.v_velocidad = campo(self, 4, "Velocidad (m/min)")
        self.v_obstaculos = tk.BooleanVar()
        ttk.Checkbutton(self, text="Hay obstáculos", variable=self.v_obstaculos).grid(
            row=5, column=1, sticky="w", padx=4)
        self.v_tobs = campo(self, 6, "Tiempo de observación (min)")
        ttk.Button(self, text="Guardar escenario", command=self._guardar).grid(
            row=7, column=1, sticky="e", padx=4, pady=4)

        columnas = (("nombre", "Nombre", 160), ("tipo", "Tipo", 100),
                    ("recursos", "Recursos", 70), ("tobs", "T. obs. (min)", 90))
        self.tabla = ttk.Treeview(
            self, columns=[c[0] for c in columnas], show="headings",
            height=5, selectmode="browse")
        for clave, texto, ancho in columnas:
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, anchor="w")
        self.tabla.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
        self.rowconfigure(8, weight=1)
        ttk.Button(self, text="Eliminar escenario seleccionado", command=self._eliminar).grid(
            row=9, column=1, sticky="e", padx=4, pady=(0, 4))

    def mostrar_empresa(self, empresa_id):
        """Muestra los escenarios de la empresa indicada (None = tabla vacía)."""
        self.empresa_id = empresa_id
        self._recargar()

    def _recargar(self):
        self.tabla.delete(*self.tabla.get_children())
        if self.empresa_id is None:
            return
        for e in database.listar_escenarios(self.empresa_id):
            t_obs = "" if e["tiempo_observacion_min"] is None else e["tiempo_observacion_min"]
            self.tabla.insert(
                "", "end", iid=str(e["id"]),
                values=(e["nombre"], e["tipo"], e["num_recursos"], t_obs))

    def _guardar(self):
        if self.empresa_id is None:
            messagebox.showwarning("Sin empresa", "Primero crea o selecciona una empresa.")
            return
        datos, errores = validaciones.validar_escenario(
            self.v_nombre.get(), self.cmb_tipo.get(), self.v_recursos.get(),
            self.v_capacidad.get(), self.v_velocidad.get(),
            self.v_obstaculos.get(), self.v_tobs.get())
        if errores:
            messagebox.showerror("Datos no válidos", "\n".join(errores))
            return
        try:
            database.crear_escenario(self.empresa_id, **datos)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Datos no válidos", "Ya existe un escenario con ese nombre en esta empresa.")
            return
        for var in (self.v_nombre, self.v_capacidad, self.v_velocidad, self.v_tobs):
            var.set("")
        self.v_recursos.set("1")
        self.v_obstaculos.set(False)
        self._recargar()
        self.on_cambio()

    def _eliminar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Selecciona un escenario de la tabla.")
            return
        if not messagebox.askyesno(
                "Confirmar", "¿Eliminar el escenario seleccionado y todos sus registros?"):
            return
        database.eliminar_escenario(int(seleccion[0]))
        self._recargar()
        self.on_cambio()