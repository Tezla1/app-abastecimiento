from PyQt6.QtWidgets import QWidget

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import PageView
from ..widgets.crud_panel import CrudPanel


class TallerView(PageView):
    def __init__(self, origenes: list[tuple]):
        super().__init__("Caracterización del taller",
                         "Registre los datos básicos del taller que alimentarán el layout, el modelo matemático y la simulación.",
                         theme.NARANJA)
        campos = [
            CampoSpec("nombre", "Nombre *", placeholder="Ej.: Taller Piloto Textil"),
            CampoSpec("area_m2", "Área (m²)", "float", 0, 1_000_000, 2),
            CampoSpec("operadores", "Operadores", "int", 0, 100_000),
            CampoSpec("jornada_h", "Jornada (h)", "float", 0.5, 24, 2, 8.0),
            CampoSpec("origen_datos", "Origen de datos", "combo"),
            CampoSpec("observaciones", "Observaciones", "multiline"),
        ]
        self.panel = CrudPanel("Datos del taller", "Talleres registrados", campos,
                               ["ID", "Nombre", "Área (m²)", "Operadores", "Jornada (h)", "Origen"],
                               theme.NARANJA, estirar=1)
        self.panel.set_opciones("origen_datos", origenes)
        self.cuerpo.addWidget(self.panel, 1)
        self.cuerpo.addWidget(self.estado)
