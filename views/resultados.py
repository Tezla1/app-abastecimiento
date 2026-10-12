from tkinter import ttk

import calculos
import database

SIN_DATOS = "—"
NOTA_VARIACION = (
    "Variación = (alternativo − base) / base × 100. En los indicadores que ya son "
    "porcentajes (utilización, solicitudes atendidas) es una variación relativa, "
    "no una diferencia en puntos porcentuales."
)


def _fmt(valor):
    return SIN_DATOS if valor is None else f"{valor:.2f}"


def _fmt_variacion(valor):
    return SIN_DATOS if valor is None else f"{valor:+.2f} %"


class ResultadosTab(ttk.Frame):
    """Indicadores de un escenario y su comparación contra otro."""

    def __init__(self, parent):
        super().__init__(parent)
        self.escenarios = []
        self.empresas = []
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ---------- Selección ----------
        seleccion = ttk.LabelFrame(self, text="Selección")
        seleccion.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        seleccion.columnconfigure(1, weight=1)

        ttk.Label(seleccion, text="Empresa").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.cmb_empresa = ttk.Combobox(seleccion, state="readonly")
        self.cmb_empresa.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self.cmb_empresa.bind("<<ComboboxSelected>>", lambda e: self._cargar_escenarios())

        ttk.Label(seleccion, text="Escenario base").grid(
            row=1, column=0, sticky="w", padx=4, pady=2)
        self.cmb_base = ttk.Combobox(seleccion, state="readonly")
        self.cmb_base.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        self.cmb_base.bind("<<ComboboxSelected>>", lambda e: self._calcular())

        ttk.Label(seleccion, text="Escenario alternativo").grid(
            row=2, column=0, sticky="w", padx=4, pady=2)
        self.cmb_alt = ttk.Combobox(seleccion, state="readonly")
        self.cmb_alt.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        self.cmb_alt.bind("<<ComboboxSelected>>", lambda e: self._calcular())

        # ---------- Tabla de resultados ----------
        marco = ttk.LabelFrame(self, text="Indicadores")
        marco.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)

        columnas = (("indicador", "Indicador", 330, "w"), ("base", "Escenario base", 150, "e"),
                    ("alt", "Escenario alternativo", 170, "e"), ("var", "Variación", 120, "e"))
        self.tabla = ttk.Treeview(
            marco, columns=[c[0] for c in columnas], show="headings",
            height=7, selectmode="none")
        for clave, texto, ancho, ancla in columnas:
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, anchor=ancla)
        self.tabla.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.lbl_resumen = ttk.Label(marco, text="")
        self.lbl_resumen.grid(row=1, column=0, sticky="w", padx=4)
        self.lbl_aviso = ttk.Label(marco, text="", foreground="#b00020", wraplength=1000)
        self.lbl_aviso.grid(row=2, column=0, sticky="w", padx=4, pady=(4, 0))
        ttk.Label(marco, text=NOTA_VARIACION, wraplength=1000).grid(
            row=3, column=0, sticky="w", padx=4, pady=4)

        self.actualizar()

    # ---------- Carga de datos ----------
    def actualizar(self):
        """Se llama al abrir la pestaña: recarga empresas y escenarios desde la base."""
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
        self._calcular()

    # ---------- Cálculo y presentación ----------
    def _calcular(self):
        self.tabla.delete(*self.tabla.get_children())
        self.lbl_resumen.config(text="")
        self.lbl_aviso.config(text="")

        base = self._escenario_en(self.cmb_base)
        alt = self._escenario_en(self.cmb_alt, desplazamiento=1)
        if base is None:
            self.lbl_aviso.config(text="Selecciona una empresa que tenga al menos un escenario.")
            return

        ind_base = calculos.calcular_indicadores(base, database.listar_registros(base["id"]))
        ind_alt = None
        if alt is not None:
            ind_alt = calculos.calcular_indicadores(alt, database.listar_registros(alt["id"]))

        avisos = []
        comparable = False
        if ind_alt is not None:
            comparable, problemas = calculos.verificar_comparable(ind_base, ind_alt)
            avisos += problemas
        if ind_alt is None:
            ind_alt = {}

        for clave, etiqueta in calculos.ETIQUETAS.items():
            v_base, v_alt = ind_base.get(clave), ind_alt.get(clave)
            variacion = calculos.variacion_pct(v_base, v_alt) if comparable else None
            self.tabla.insert("", "end", values=(
                etiqueta, _fmt(v_base), _fmt(v_alt), _fmt_variacion(variacion)))

        resumen = f'Base: {ind_base["n_registros"]} registros ({ind_base["n_atendidas"]} atendidos)'
        if alt is not None:
            resumen += (f'   |   Alternativo: {ind_alt["n_registros"]} registros '
                        f'({ind_alt["n_atendidas"]} atendidos)')
        self.lbl_resumen.config(text=resumen)

        for nombre, ind in (("base", ind_base), ("alternativo", ind_alt)):
            util = ind.get("utilizacion_pct")
            if util is not None and util > 100:
                avisos.append(
                    f"La utilización del escenario {nombre} supera el 100 %: revisa el "
                    "tiempo de observación o el número de recursos.")
        self.lbl_aviso.config(text="\n".join(avisos))