import sqlite3
from tkinter import messagebox, ttk

import database
import validaciones
from views.widgets import campo


class PanelEmpresa(ttk.LabelFrame):
    """Selector de empresa activa y formulario para crear empresas."""

    def __init__(self, parent, on_empresa_cambiada):
        super().__init__(parent, text="Empresa")
        # Se llama con el id de la empresa activa (o None) cada vez que cambia
        self.on_empresa_cambiada = on_empresa_cambiada
        self.empresas = []
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Empresa activa").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.cmb_empresa = ttk.Combobox(self, state="readonly")
        self.cmb_empresa.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self.cmb_empresa.bind("<<ComboboxSelected>>", lambda e: self._notificar())
        ttk.Button(self, text="Eliminar", command=self._eliminar).grid(row=0, column=2, padx=4)

        ttk.Separator(self).grid(row=1, column=0, columnspan=3, sticky="ew", pady=6)
        self.v_nombre = campo(self, 2, "Nombre")
        self.v_area = campo(self, 3, "Área (m²)")
        self.v_estaciones = campo(self, 4, "N.º de estaciones")
        self.v_operarios = campo(self, 5, "N.º de operarios")
        ttk.Button(self, text="Guardar empresa", command=self._guardar).grid(
            row=6, column=1, sticky="e", padx=4, pady=4)

    def empresa_id(self):
        indice = self.cmb_empresa.current()
        return self.empresas[indice]["id"] if indice >= 0 else None

    def cargar(self, seleccionar_id=None):
        self.empresas = database.listar_empresas()
        self.cmb_empresa["values"] = [e["nombre"] for e in self.empresas]
        if self.empresas:
            ids = [e["id"] for e in self.empresas]
            self.cmb_empresa.current(ids.index(seleccionar_id) if seleccionar_id in ids else 0)
        else:
            self.cmb_empresa.set("")
        self._notificar()

    def _notificar(self):
        self.on_empresa_cambiada(self.empresa_id())

    def _guardar(self):
        datos, errores = validaciones.validar_empresa(
            self.v_nombre.get(), self.v_area.get(),
            self.v_estaciones.get(), self.v_operarios.get())
        if errores:
            messagebox.showerror("Datos no válidos", "\n".join(errores))
            return
        try:
            nueva_id = database.crear_empresa(**datos)
        except sqlite3.IntegrityError:
            messagebox.showerror("Datos no válidos", "Ya existe una empresa con ese nombre.")
            return
        for var in (self.v_nombre, self.v_area, self.v_estaciones, self.v_operarios):
            var.set("")
        self.cargar(seleccionar_id=nueva_id)

    def _eliminar(self):
        empresa_id = self.empresa_id()
        if empresa_id is None:
            messagebox.showwarning("Sin empresa", "No hay una empresa seleccionada.")
            return
        if not messagebox.askyesno(
                "Confirmar",
                f"¿Eliminar la empresa «{self.cmb_empresa.get()}»?\n"
                "Se borrarán también sus escenarios y registros."):
            return
        database.eliminar_empresa(empresa_id)
        self.cargar()