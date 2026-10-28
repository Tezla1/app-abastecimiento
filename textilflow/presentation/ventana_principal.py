from typing import Optional, Sequence

from PyQt6.QtCore import QCoreApplication, QEvent, QSettings, Qt, pyqtSignal
from PyQt6.QtWidgets import (QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

from . import theme
from ..version import NOMBRE, SUBTITULO, VERSION
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QGuiApplication

from .widgets.adaptable import FilaAdaptable
from .widgets.iconos import icono as icono_seccion
from .widgets.logo import logo_icono, logo_pixmap


class VentanaPrincipal(QMainWindow):
    pagina_cambiada = pyqtSignal(int)
    taller_elegido = pyqtSignal(object)
    alertas_solicitadas = pyqtSignal()
    tema_solicitado = pyqtSignal()

    def __init__(self, paginas: Sequence[tuple]):
        super().__init__()
        self.setWindowTitle(f"{NOMBRE} v{VERSION} · Optimización de procesos industriales e intralogística")
        self.setWindowIcon(logo_icono())
        self.setMinimumSize(640, 420)
        if not self.restaurar_geometria():
            self._ajustar_a_pantalla()
        self.armar(paginas)

    antes_de_cerrar = None

    def closeEvent(self, ev) -> None:
        if self.antes_de_cerrar is not None and not self.antes_de_cerrar():
            ev.ignore()
            return
        self.guardar_geometria()
        super().closeEvent(ev)

    def guardar_geometria(self) -> None:
        try:
            a = QSettings("TextilFlow", "TextilFlow")
            a.setValue("geometria", self.saveGeometry())
            a.setValue("maximizada", self.isMaximized())
        except Exception:
            pass

    def restaurar_geometria(self) -> bool:
        a = QSettings("TextilFlow", "TextilFlow")
        g = a.value("geometria")
        if g is None or not self.restoreGeometry(g):
            return False
        visible = any(p.availableGeometry().intersects(self.frameGeometry()) for p in QGuiApplication.screens())
        if not visible or self.width() < 640 or self.height() < 420:
            return False
        if str(a.value("maximizada", "false")).lower() == "true":
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        return True

    def _ajustar_a_pantalla(self) -> None:
        pantalla = QGuiApplication.primaryScreen()
        if pantalla is None:
            self.resize(1360, 840)
            return
        area = pantalla.availableGeometry()
        w, h = min(1360, int(area.width() * 0.96)), min(840, int(area.height() * 0.94))
        self.resize(max(w, 640), max(h, 420))
        self.move(area.x() + (area.width() - self.width()) // 2, area.y() + (area.height() - self.height()) // 2)

    def armar(self, paginas: Sequence[tuple]) -> None:
        raiz = QWidget()
        raiz.setObjectName("raiz")
        self.setCentralWidget(raiz)
        lay = QHBoxLayout(raiz)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lateral = QFrame()
        lateral.setObjectName("sidebar")
        lateral.setMinimumWidth(240)
        ll = QVBoxLayout(lateral)
        ll.setContentsMargins(12, 16, 12, 12)
        cabecera = QHBoxLayout()
        icono = QLabel()
        icono.setPixmap(logo_pixmap(44))
        cabecera.addWidget(icono)
        textos = QVBoxLayout()
        marca = self._marca = QLabel(NOMBRE)
        marca.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = self._sub = QLabel(f"{SUBTITULO}")
        sub.setObjectName("tenue")
        sub.setWordWrap(True)
        textos.addWidget(marca)
        textos.addWidget(sub)
        cabecera.addLayout(textos, 1)
        ll.addLayout(cabecera)
        version = self._version = QLabel(f"Versión {VERSION}")
        version.setStyleSheet(f"color: {theme.TURQUESA}; font-weight: 700;")
        ll.addWidget(version)
        ll.addSpacing(10)
        self._etiquetas = []
        self._compacto = None
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._pila = QStackedWidget()
        for i, (etiqueta, color, widget) in enumerate(paginas):
            b = QPushButton(f" {etiqueta}")
            b.setObjectName("nav")
            b.setIcon(icono_seccion(etiqueta, color))
            b.setIconSize(QSize(20, 20))
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton#nav {{ border-left: 4px solid {color}; }}"
                            f"QPushButton#nav:checked {{ background: {theme.PANEL_2}; border-left: 4px solid {color}; }}")
            b.setToolTip(etiqueta)
            self._etiquetas.append(etiqueta)
            self._grupo.addButton(b, i)
            ll.addWidget(b)
            self._pila.addWidget(widget)
        ll.addStretch(1)
        pie = self._pie = QLabel(f"{NOMBRE} v{VERSION}\nSimulación de procesos · calculos.py")
        pie.setObjectName("tenue")
        ll.addWidget(pie)
        lateral_scroll = QScrollArea()
        lateral_scroll.setObjectName("lateral_scroll")
        lateral_scroll.setWidgetResizable(True)
        lateral_scroll.setFrameShape(QFrame.Shape.NoFrame)
        lateral_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._lateral_scroll = lateral_scroll
        lateral_scroll.setFixedWidth(256)
        lateral_scroll.setWidget(lateral)
        lay.addWidget(lateral_scroll)

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
        claro = theme.tema_actual() == "claro"
        self.btn_tema = QPushButton(" Tema oscuro" if claro else " Tema claro")
        self.btn_tema.setIcon(icono_seccion("Luna" if claro else "Sol", theme.TEXTO, 16))
        self.btn_tema.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tema.setToolTip("Cambiar entre tema claro y oscuro")
        self.btn_tema.setStyleSheet(f"QPushButton {{ border: 1px solid {theme.BORDE}; border-radius: 12px; padding: 4px 12px; }}")
        self.btn_tema.clicked.connect(self.tema_solicitado.emit)
        cl.addWidget(self.btn_tema)
        self._lbl_taller = QLabel("   Taller activo:")
        cl.addWidget(self._lbl_taller)
        self.combo_taller = QComboBox()
        self.combo_taller.setMinimumWidth(150)
        self.combo_taller.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.combo_taller.setMaximumWidth(420)
        cl.addWidget(self.combo_taller)
        self.estado = QLabel("● READY")
        self.estado.setStyleSheet(f"color: {theme.VERDE}; font-weight: 700; padding-left: 12px;")
        cl.addWidget(self.estado)
        der.addWidget(cab)
        der.addWidget(self._pila, 1)
        lay.addLayout(der, 1)

        self._alertas_txt = None
        self._compacto = None
        self._aplicar_compacto(self.width() < 980)
        self._grupo.idClicked.connect(self._ir)
        self.combo_taller.activated.connect(lambda _: self.taller_elegido.emit(self.combo_taller.currentData()))
        self._grupo.button(0).setChecked(True)

    def resizeEvent(self, ev) -> None:
        super().resizeEvent(ev)
        if hasattr(self, "_etiquetas"):
            self._aplicar_compacto(self.width() < 980)
            FilaAdaptable.actualizar(self.width() - (64 if self._compacto else 256) - 48 - 14)

    def _aplicar_compacto(self, compacto: bool) -> None:
        if compacto == self._compacto:
            return
        self._compacto = compacto
        for i, b in enumerate(self._grupo.buttons()):
            b.setText("" if compacto else f" {self._etiquetas[i]}")
        for w in (self._marca, self._sub, self._version, self._pie):
            w.setVisible(not compacto)
        self._lateral_scroll.setFixedWidth(64 if compacto else 256)
        self._lbl_taller.setVisible(not compacto)
        self.btn_tema.setText("" if compacto else (" Tema oscuro" if theme.tema_actual() == "claro" else " Tema claro"))
        self._pintar_alertas()

    def poner_pagina(self, i: int, widget: QWidget) -> None:
        marcador = self._pila.widget(i)
        actual = self._pila.currentIndex()
        self._pila.removeWidget(marcador)
        area = QScrollArea()
        area.setObjectName("desplazable")
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setWidget(widget)
        self._pila.insertWidget(i, area)
        self._pila.setCurrentIndex(actual)
        marcador.deleteLater()

    def vaciar(self) -> None:
        viejo = self.takeCentralWidget()
        if viejo is not None:
            viejo.hide()
            viejo.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def _ir(self, i: int) -> None:
        self._pila.setCurrentIndex(i)
        self.pagina_cambiada.emit(i)

    def seleccionar(self, i: int) -> None:
        self._grupo.button(i).setChecked(True)
        self._pila.setCurrentIndex(i)

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
        self._alertas_txt = (total, criticas, altas)
        self._pintar_alertas()

    def _pintar_alertas(self) -> None:
        if not getattr(self, "_alertas_txt", None):
            return
        total, criticas, altas = self._alertas_txt
        color = theme.ROJO if criticas else theme.NARANJA if altas else theme.VERDE if total == 0 else theme.DORADO
        detalle = f"{criticas} críticas · {altas} altas" if total else "sin alertas"
        self.insignia.setToolTip(f"Alertas: {total} ({detalle})")
        self.insignia.setText(f"🔔 {total}" if self._compacto else f"🔔 Alertas: {total}  ({detalle})")
        self.insignia.setStyleSheet(f"QPushButton {{ border: 1px solid {color}; color: {color}; border-radius: 12px; "
                                    f"padding: 4px 12px; font-weight: 700; }}")
