BG = "#0B1220"
PANEL = "#101A2E"
PANEL_2 = "#15233D"
BORDE = "#22345A"
TEXTO = "#E6EDF7"
TENUE = "#8FA0BC"

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
COLOR_NIVEL = {"CRÍTICA": ROJO, "ALTA": NARANJA, "MEDIA": DORADO, "INFO": TENUE}
COLOR_RECURSOS = ["#5CC8FF", "#FF7AC6", "#B6F36A", "#FFD166", "#C49BFF", "#FF9F6B", "#6BE3B2", "#F2F2F2"]

ESCALA_CALOR = [(0.0, "#2F6BDE"), (0.35, "#1BA39C"), (0.6, "#E8D21F"), (0.8, "#F29A1F"), (1.0, "#E5484D")]


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

QFrame#sidebar {{ background: {PANEL}; border-right: 1px solid {BORDE}; }}
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
QPushButton#primario {{ background: {acento}; border-color: {acento}; font-weight: 600; }}
QPushButton#primario:hover {{ opacity: 0.9; }}
QPushButton#peligro {{ background: #5A2530; border-color: {ROJO}; }}

QTableWidget {{ background: {BG}; alternate-background-color: #0E1830; border: 1px solid {BORDE};
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
