# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Página de Caracterización del taller.

from PyQt6.QtWidgets import QWidget

from .. import theme
from ..viewmodels import CampoSpec
from ..widgets.common import VistaPagina
from ..widgets.panel_crud import PanelCrud


class TallerView(VistaPagina):
    def __init__(self, origenes: list[tuple]):
        super().__init__("Caracterización del taller",
                         "Registre los datos básicos del taller que alimentarán el layout, el modelo matemático y la simulación.",
                         theme.NARANJA)
        campos = [
            CampoSpec("nombre", "Nombre *", placeholder="Ej.: Taller Piloto Textil", ayuda="Nombre que identifica al taller (único). Ej.: «Confecciones Andina». Es obligatorio."),
            CampoSpec("area_m2", "Área (m²)", "float", 0, 1_000_000, 2, ayuda="Área total de producción en metros cuadrados (m²): largo × ancho del piso útil del taller. Ej.: una nave de 20 m × 12 m = 240 m²."),
            CampoSpec("operadores", "Operadores", "int", 0, 100_000, ayuda="Número de personas que trabajan en la planta (operarios de corte, costura, inspección, empaque, etc.). Entero ≥ 0."),
            CampoSpec("jornada_h", "Jornada (h)", "float", 0.5, 24, 2, 8.0, ayuda="Horas de trabajo por turno o jornada diaria, de 0,5 a 24 h. Ej.: 8 h. Se usa para calcular la capacidad disponible."),
            CampoSpec("origen_datos", "Origen de datos", "combo", ayuda="De dónde vienen los datos: «Real» si se midieron en el taller, «Sintético» si son supuestos o de ejemplo, «Diseño / conceptual» si son de una propuesta de diseño."),
            CampoSpec("observaciones", "Observaciones", "multiline", ayuda="Notas libres sobre el taller (condiciones, supuestos, fuente de los datos). Opcional."),
        ]
        self.panel = PanelCrud("Datos del taller", "Talleres registrados", campos,
                               ["ID", "Nombre", "Área (m²)", "Operadores", "Jornada (h)", "Origen"],
                               theme.NARANJA, estirar=1)
        self.panel.set_opciones("origen_datos", origenes)
        self.cuerpo.addWidget(self.panel, 1)
        self.cuerpo.addWidget(self.estado)
