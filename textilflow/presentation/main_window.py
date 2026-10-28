from typing import Optional, Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from . import theme
from ..version import NOMBRE, SUBTITULO, VERSION
from PyQt6.QtCore import QSize

from .widgets.iconos import icono as icono_seccion
from .widgets.logo import logo_icono, logo_pixmap


class MainWindow(QMainWindow):
    pagina_cambiada = pyqtSignal(int)
    taller_elegido = pyqtSignal(object)
    alertas_solicitadas = pyqtSignal()

    def __init__(self, paginas: Sequence[tuple]):
        super().__init__()
        self.setWindowTitle(f"{NOMBRE} v{VERSION} · Optimización de procesos industriales e intralogística")
        self.setWindowIcon(logo_icono())
        self.resize(1360, 840)
        raiz = QWidget()
        raiz.setObjectName("raiz")
        self.setCentralWidget(raiz)
        lay = QHBoxLayout(raiz)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lateral = QFrame()
        lateral.setObjectName("sidebar")
        lateral.setFixedWidth(256)
        ll = QVBoxLayout(lateral)
        ll.setContentsMargins(12, 16, 12, 12)
        cabecera = QHBoxLayout()
        icono = QLabel()
        icono.setPixmap(logo_pixmap(44))
        cabecera.addWidget(icono)
        textos = QVBoxLayout()
        marca = QLabel(NOMBRE)
        marca.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel(f"{SUBTITULO}")
        sub.setObjectName("tenue")
        sub.setWordWrap(True)
        textos.addWidget(marca)
        textos.addWidget(sub)
        cabecera.addLayout(textos, 1)
        ll.addLayout(cabecera)
        version = QLabel(f"Versión {VERSION}")
        version.setStyleSheet(f"color: {theme.TURQUESA}; font-weight: 700;")
        ll.addWidget(version)
        ll.addSpacing(10)
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._pila = QStackedWidget()
        for i, (etiqueta, color, widget) in enumerate(paginas):
            b = QPushButton(f" {etiqueta}")
            b.setObjectName("nav")
            # el icono toma el color de la sección
            b.setIcon(icono_seccion(etiqueta, color))
            b.setIconSize(QSize(20, 20))
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton#nav {{ border-left: 4px solid {color}; }}"
                            f"QPushButton#nav:checked {{ background: {theme.PANEL_2}; border-left: 4px solid {color}; }}")
            self._grupo.addButton(b, i)
            ll.addWidget(b)
            self._pila.addWidget(widget)
        ll.addStretch(1)
        pie = QLabel(f"{NOMBRE} v{VERSION}\nSimulación de procesos · calculos.py")
        pie.setObjectName("tenue")
        ll.addWidget(pie)
        lay.addWidget(lateral)

        der = QVBoxLayout()
        der.setContentsMargins(0, 0, 0, 0)
        cab = QFrame()
        cab.setStyleSheet(f"background: {theme.PANEL}; border-bottom: 1px solid {theme.BORDE};")
        cl = QHBoxLayout(cab)
        cl.setContentsMargins(24, 8, 24, 8)
        cl.addStretch(1)
        self.insignia = QPushButton("🔔 Alertas: —")
        self.insignia.setCursor(Qt.CursorShape.PointingHandCursor)
        self.insignia.setStyleSheet(f"QPushButton {{ border: 1px solid {theme.BORDE}; border-radius: 12px; padding: 4px 12px; "
                                    f"font-weight: 700; }}")
        self.insignia.clicked.connect(self.alertas_solicitadas.emit)
        cl.addWidget(self.insignia)
        cl.addWidget(QLabel("   Taller activo:"))
        self.combo_taller = QComboBox()
        self.combo_taller.setMinimumWidth(320)
        cl.addWidget(self.combo_taller)
        self.estado = QLabel("● READY")
        self.estado.setStyleSheet(f"color: {theme.VERDE}; font-weight: 700; padding-left: 12px;")
        cl.addWidget(self.estado)
        der.addWidget(cab)
        der.addWidget(self._pila, 1)
        lay.addLayout(der, 1)

        self._grupo.idClicked.connect(self._ir)
        self.combo_taller.activated.connect(lambda _: self.taller_elegido.emit(self.combo_taller.currentData()))
        self._grupo.button(0).setChecked(True)

    def _ir(self, i: int) -> None:
        self._pila.setCurrentIndex(i)
        self.pagina_cambiada.emit(i)

    def ir_a(self, i: int) -> None:
        self._grupo.button(i).setChecked(True)
        self._ir(i)

    def pagina_actual(self) -> int:
        return self._pila.currentIndex()

    def set_talleres(self, opciones: Sequence[tuple], activo: Optional[int]) -> None:
        self.combo_taller.blockSignals(True)
        self.combo_taller.clear()
        if not opciones:
            self.combo_taller.addItem("— Sin talleres —", None)
        for id_, nombre in opciones:
            self.combo_taller.addItem(nombre, id_)
        i = self.combo_taller.findData(activo)
        self.combo_taller.setCurrentIndex(max(i, 0))
        self.combo_taller.blockSignals(False)

    def set_alertas(self, total: int, criticas: int, altas: int) -> None:
        color = theme.ROJO if criticas else theme.NARANJA if altas else theme.VERDE if total == 0 else theme.DORADO
        detalle = f"{criticas} críticas · {altas} altas" if total else "sin alertas"
        self.insignia.setText(f"🔔 Alertas: {total}  ({detalle})")
        self.insignia.setStyleSheet(f"QPushButton {{ border: 1px solid {color}; color: {color}; border-radius: 12px; "
                                    f"padding: 4px 12px; font-weight: 700; }}")
