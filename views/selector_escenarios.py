from tkinter import ttk

import database


class SelectorEscenarios(ttk.LabelFrame):
    """Combos de empresa, escenario base y escenario alternativo."""

    def __init__(self, parent, on_cambio):
        super().__init__(parent, text="Selección")
        self.on_cambio = on_cambio  # se llama cada vez que cambia la selección
        self.empresas = []
        self.escenarios = []
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Empresa").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.cmb_empresa = ttk.Combobox(self, state="readonly")
        self.cmb_empresa.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self.cmb_empresa.bind("<<ComboboxSelected>>", lambda e: self._cargar_escenarios())

        ttk.Label(self, text="Escenario base").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        self.cmb_base = ttk.Combobox(self, state="readonly")
        self.cmb_base.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        self.cmb_base.bind("<<ComboboxSelected>>", lambda e: self.on_cambio())

        ttk.Label(self, text="Escenario alternativo").grid(
            row=2, column=0, sticky="w", padx=4, pady=2)
        self.cmb_alt = ttk.Combobox(self, state="readonly")
        self.cmb_alt.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        self.cmb_alt.bind("<<ComboboxSelected>>", lambda e: self.on_cambio())

    def seleccion(self):
        """Devuelve (escenario_base, escenario_alternativo); cada uno es un dict o None."""
        return (self._escenario_en(self.cmb_base),
                self._escenario_en(self.cmb_alt, desplazamiento=1))
    def empresa(self):
        """Empresa elegida (dict) o None."""
        indice = self.cmb_empresa.current()
        return self.empresas[indice] if 0 <= indice < len(self.empresas) else None

    def actualizar(self):
        """Recarga empresas y escenarios desde la base, conservando la selección si existe."""
        empresa_previa = self._empresa_id()
        self.empresas = database.listar_empresas()
        self.cmb_empresa["values"] = [e["nombre"] for e in self.empresas]
        if self.empresas:
            ids = [e["id"] for e in self.empresas]
            self.cmb_empresa.current(ids.index(empresa_previa) if empresa_previa in ids else 0)
        else:
            self.cmb_empresa.set("")
        self._cargar_escenarios()

    def _empresa_id(self):
        indice = self.cmb_empresa.current()
        return self.empresas[indice]["id"] if 0 <= indice < len(self.empresas) else None

    def _escenario_en(self, combo, desplazamiento=0):
        """Escenario elegido en un combo (el alternativo tiene una opción extra al inicio)."""
        indice = combo.current() - desplazamiento
        return self.escenarios[indice] if 0 <= indice < len(self.escenarios) else None

    def _cargar_escenarios(self):
        # Se leen las selecciones previas antes de reemplazar la lista
        previo_base = self._escenario_en(self.cmb_base)
        previo_alt = self._escenario_en(self.cmb_alt, desplazamiento=1)
        base_previo = previo_base["id"] if previo_base else None
        alt_previo = previo_alt["id"] if previo_alt else None

        empresa_id = self._empresa_id()
        self.escenarios = database.listar_escenarios(empresa_id) if empresa_id else []
        etiquetas = [f'{e["nombre"]} ({e["tipo"]})' for e in self.escenarios]
        self.cmb_base["values"] = etiquetas
        self.cmb_alt["values"] = ["(sin comparar)"] + etiquetas

        ids = [e["id"] for e in self.escenarios]
        if not ids:
            self.cmb_base.set("")
            self.cmb_alt.set("")
        else:
            if base_previo in ids:
                i_base = ids.index(base_previo)
            else:  # por defecto: el primer escenario de tipo Base, o el primero
                i_base = next(
                    (i for i, e in enumerate(self.escenarios) if e["tipo"] == "Base"), 0)
            self.cmb_base.current(i_base)

            if alt_previo in ids and alt_previo != ids[i_base]:
                i_alt = ids.index(alt_previo) + 1
            else:  # por defecto: el primer escenario distinto del base
                otros = [i for i in range(len(ids)) if i != i_base]
                i_alt = otros[0] + 1 if otros else 0
            self.cmb_alt.current(i_alt)
        self.on_cambio()