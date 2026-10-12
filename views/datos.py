from tkinter import ttk

from views.datos_empresa import PanelEmpresa
from views.datos_escenarios import PanelEscenarios
from views.datos_registros import PanelRegistros


class DatosTab(ttk.Frame):
    """Pestaña 'Ingresar datos': arma los paneles y conecta uno con otro."""

    def __init__(self, parent, on_cambio=None):
        super().__init__(parent)
        # Se llamará cuando cambien los datos, para refrescar las otras pestañas
        self.on_cambio = on_cambio or (lambda: None)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        izquierda = ttk.Frame(self)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        derecha = ttk.Frame(self)
        derecha.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        self.panel_registros = PanelRegistros(derecha, on_cambio=self.on_cambio)
        self.panel_escenarios = PanelEscenarios(
            izquierda, on_cambio=self.on_cambio, on_seleccion=self._escenario_seleccionado)
        self.panel_empresa = PanelEmpresa(izquierda, on_empresa_cambiada=self._empresa_cambiada)

        self.panel_empresa.pack(fill="x", pady=(0, 8))
        self.panel_escenarios.pack(fill="both", expand=True)
        self.panel_registros.pack(fill="both", expand=True)

        self.panel_empresa.cargar()

    def _empresa_cambiada(self, empresa_id):
        self.panel_escenarios.mostrar_empresa(empresa_id)
        self.on_cambio()

    def _escenario_seleccionado(self, escenario_id, nombre):
        self.panel_registros.mostrar_escenario(escenario_id, nombre)