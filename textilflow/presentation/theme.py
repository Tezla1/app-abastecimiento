# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Colores, tipografía y hoja de estilo de los temas claro y oscuro, más funciones de formato de números.

PALETAS = {
    "oscuro": dict(BG="#202020", PANEL="#2B2B2B", PANEL_2="#363636", BORDE="#404040", TEXTO="#F3F3F3",
                   LIENZO="#1B1B1B", TRAZO="#7A7A7A", TRAZO_OFF="#4A4A4A", FILA_ALT="#262626", RESALTE="#FFD166",
                   RUTA="#D0D0D0", DOC_TITULO="#F3F3F3", DOC_TEXTO="#D0D0D0", DOC_ENLACE="#60CDFF", DOC_CODIGO="#FFD166",
                   PELIGRO_BG="#442726", CUADRICULA="#2E2E2E", TENUE="#9D9D9D"),
    "claro": dict(BG="#F1F4FA", PANEL="#FFFFFF", PANEL_2="#E6ECF6", BORDE="#C9D3E4", TEXTO="#1B2638",
                  LIENZO="#E9EEF7", TRAZO="#8C9BB8", TRAZO_OFF="#C3CDE0", FILA_ALT="#F6F8FC", RESALTE="#C27A00",
                  RUTA="#53627F", DOC_TITULO="#1B2638", DOC_TEXTO="#34425C", DOC_ENLACE="#1F55C4", DOC_CODIGO="#9A5B00",
                  PELIGRO_BG="#F8DADD", CUADRICULA="#DCE3F0", TENUE="#6F809C"),
}
_actual = "oscuro"
globals().update(PALETAS["oscuro"])

AZUL = "#2F6BDE"
VERDE = "#1FA971"
NARANJA = "#F29A1F"
MORADO = "#8E5BD6"
ROJO = "#C0444F"
TURQUESA = "#1BA39C"
DORADO = "#D9A21B"

COLOR_FUNCION = {
    "ALMACEN": NARANJA,
    "DESPACHO": VERDE,
    "PROCESO": "#2A8FD6",
    "ESPERA": MORADO,
    "BASE": TURQUESA,
}

COLOR_ESTADO = {"PASS": VERDE, "WARNING": NARANJA, "FAIL": ROJO}
ESTADO_ES = {"PASS": "APROBADO", "WARNING": "ADVERTENCIA", "FAIL": "FALLA"}
COLOR_NIVEL = {"CRÍTICA": ROJO, "ALTA": NARANJA, "MEDIA": DORADO, "INFO": TENUE}
COLOR_RECURSOS = ["#5CC8FF", "#FF7AC6", "#B6F36A", "#FFD166", "#C49BFF", "#FF9F6B", "#6BE3B2", "#F2F2F2"]

ESCALA_CALOR = [(0.0, "#2F6BDE"), (0.35, "#1BA39C"), (0.6, "#E8D21F"), (0.8, "#F29A1F"), (1.0, "#E5484D")]


def aplicar(nombre: str) -> None:
    global _actual
    if nombre not in PALETAS:
        nombre = "oscuro"
    _actual = nombre
    globals().update(PALETAS[nombre])
    COLOR_NIVEL["INFO"] = TENUE


def tema_actual() -> str:
    return _actual


def color_calor(x: float) -> str:
    x = min(1.0, max(0.0, x))
    for (a, ca), (b, cb) in zip(ESCALA_CALOR, ESCALA_CALOR[1:]):
        if x <= b:
            f = (x - a) / (b - a) if b > a else 0.0
            ra, ga, ba = int(ca[1:3], 16), int(ca[3:5], 16), int(ca[5:7], 16)
            rb, gb, bb = int(cb[1:3], 16), int(cb[3:5], 16), int(cb[5:7], 16)
            return "#%02X%02X%02X" % (round(ra + (rb - ra) * f), round(ga + (gb - ga) * f), round(ba + (bb - ba) * f))
    return ESCALA_CALOR[-1][1]


GRADIENTE_CSS = "qlineargradient(x1:0, y1:0, x2:1, y2:0, " + ", ".join(
    f"stop:{a} {c}" for a, c in ESCALA_CALOR) + ")"


def fmt(valor, decimales: int = 2, sufijo: str = "") -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{decimales}f}{sufijo}"


def hoja_de_estilo(acento: str = AZUL) -> str:
    return f"""
* {{ font-family: 'Segoe UI', 'Noto Sans', 'DejaVu Sans', sans-serif; font-size: 12px; color: {TEXTO}; }}
QMainWindow, QWidget#raiz, QWidget#pagina {{ background: {BG}; }}
QLabel {{ background: transparent; }}
QLabel#titulo {{ font-size: 24px; font-weight: 700; }}
QLabel#subtitulo, QLabel#tenue {{ color: {TENUE}; }}
QLabel#estado {{ color: {TENUE}; padding: 4px 0; }}

QDialog, QMessageBox, QProgressDialog, QInputDialog {{ background: {BG}; }}
QProgressBar {{ background: {PANEL_2}; border: 1px solid {BORDE}; border-radius: 6px; text-align: center; min-height: 18px; }}
QProgressBar::chunk {{ background: {AZUL}; border-radius: 5px; }}
QFrame#sidebar {{ background: {PANEL}; border-right: 1px solid {BORDE}; }}
QScrollArea#desplazable, QScrollArea#desplazable > QWidget > QWidget {{ background: {BG}; border: none; }}
QScrollArea#lateral_scroll, QScrollArea#lateral_scroll > QWidget > QWidget {{ background: {PANEL}; border: none; }}
QPushButton#nav {{ text-align: left; padding: 10px 8px; border: none; border-radius: 8px;
    background: transparent; color: {TEXTO}; }}
QPushButton#nav:hover {{ background: {PANEL_2}; }}
QPushButton#nav:checked {{ background: {AZUL}; font-weight: 600; }}

QFrame#tarjeta, QGroupBox {{ background: {PANEL}; border: 1px solid {BORDE}; border-radius: 10px; }}
QGroupBox {{ margin-top: 14px; padding: 14px 10px 10px 10px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {TEXTO}; }}

QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {BG}; border: 1px solid {BORDE}; border-radius: 6px; padding: 5px 8px;
    selection-background-color: {AZUL}; }}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {acento}; }}
QComboBox QAbstractItemView {{ background: {PANEL}; selection-background-color: {AZUL}; border: 1px solid {BORDE}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QCheckBox {{ spacing: 8px; }}

QPushButton {{ background: {PANEL_2}; border: 1px solid {BORDE}; border-radius: 6px; padding: 7px 14px; }}
QPushButton:hover {{ border-color: {acento}; }}
QPushButton:disabled {{ color: {TENUE}; }}
QPushButton#primario {{ background: {acento}; border-color: {acento}; font-weight: 600; color: white; }}
QPushButton#primario:hover {{ opacity: 0.9; }}
QPushButton#peligro {{ background: {PELIGRO_BG}; border-color: {ROJO}; }}

QTableWidget {{ background: {BG}; alternate-background-color: {FILA_ALT}; border: 1px solid {BORDE};
    border-radius: 8px; gridline-color: transparent; selection-background-color: {AZUL}; }}
QTableWidget::item {{ padding: 4px 8px; }}
QHeaderView::section {{ background: {PANEL_2}; border: none; border-bottom: 1px solid {BORDE};
    padding: 7px 8px; font-weight: 600; }}

QTabWidget::pane {{ border: none; top: 6px; }}
QTabBar::tab {{ background: {PANEL}; border: 1px solid {BORDE}; border-radius: 6px; padding: 7px 14px; margin-right: 6px; }}
QTabBar::tab:selected {{ background: {acento}; border-color: {acento}; font-weight: 600; }}

QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDE}; border-radius: 5px; min-height: 24px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {BORDE}; border-radius: 5px; min-width: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QToolTip {{ background: {PANEL_2}; color: {TEXTO}; border: 1px solid {BORDE}; }}
"""
