from typing import Optional, Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QScrollArea, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
                             QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout,
                             QWidget)

from ..viewmodels import CampoSpec
from .common import TablaDatos
from .adaptable import FilaAdaptable


class PanelCrud(QWidget):
    guardar_solicitado = pyqtSignal(dict)
    eliminar_solicitado = pyqtSignal(int)
    seleccionado = pyqtSignal(int)
    nuevo_solicitado = pyqtSignal()

    def __init__(self, titulo_form: str, titulo_tabla: str, campos: Sequence[CampoSpec],
                 encabezados: Sequence[str], acento: str, ancho_form: int = 340,
                 estirar: Optional[int] = None, parent=None):
        super().__init__(parent)
        self._campos = {c.nombre: c for c in campos}
        self._widgets: dict[str, QWidget] = {}
        self._id: Optional[int] = None

        raiz = FilaAdaptable(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(12)

        form_box = QFrame()
        form_box.setObjectName("tarjeta")
        fl = QVBoxLayout(form_box)
        cab = QLabel(titulo_form)
        cab.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {acento}; padding-left: 8px;")
        fl.addWidget(cab)
        formulario = QFormLayout()
        formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        formulario.setVerticalSpacing(10)
        formulario.setHorizontalSpacing(12)
        formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        for c in campos:
            w = self._crear_widget(c)
            self._widgets[c.nombre] = w
            formulario.addRow(c.etiqueta, w)
            if c.ayuda:
                w.setToolTip(c.ayuda)
                w.setWhatsThis(c.ayuda)
                etiqueta = formulario.labelForField(w)
                if etiqueta is not None:
                    etiqueta.setToolTip(c.ayuda)
                    etiqueta.setCursor(Qt.CursorShape.WhatsThisCursor)
        marco = QWidget()
        envoltorio = QVBoxLayout(marco)
        envoltorio.setContentsMargins(0, 4, 0, 0)
        envoltorio.addLayout(formulario)
        envoltorio.addStretch(1)
        marco.setObjectName("formscroll")
        marco.setStyleSheet("QWidget#formscroll { background: transparent; }")
        desplazable = QScrollArea()
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        desplazable.setStyleSheet("QScrollArea { background: transparent; }")
        desplazable.setWidget(marco)
        fl.addWidget(desplazable, 1)
        self._form_layout = fl
        botones = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("peligro")
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("primario")
        for b in (self.btn_nuevo, self.btn_eliminar, self.btn_guardar):
            botones.addWidget(b)
        fl.addLayout(botones)
        raiz.fijar_ancho(form_box, ancho_form)
        raiz.addWidget(form_box)

        tabla_box = QFrame()
        tabla_box.setObjectName("tarjeta")
        tl = QVBoxLayout(tabla_box)
        cab2 = QLabel(titulo_tabla)
        cab2.setStyleSheet(f"font-size: 14px; font-weight: 700; border-left: 3px solid {acento}; padding-left: 8px;")
        tl.addWidget(cab2)
        self.tabla = TablaDatos(encabezados, estirar=estirar)
        tl.addWidget(self.tabla)
        raiz.addWidget(tabla_box, 1)

        self.btn_guardar.clicked.connect(lambda: self.guardar_solicitado.emit(self.valores()))
        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.tabla.fila_seleccionada.connect(lambda i: i is not None and self.seleccionado.emit(int(i)))

    def _crear_widget(self, c: CampoSpec) -> QWidget:
        if c.tipo == "int":
            w = QSpinBox()
            w.setRange(int(c.minimo), int(c.maximo))
            w.setValue(int(c.defecto or c.minimo))
        elif c.tipo == "float":
            w = QDoubleSpinBox()
            w.setRange(c.minimo, c.maximo)
            w.setDecimals(c.decimales)
            w.setValue(float(c.defecto or 0))
        elif c.tipo == "combo":
            w = QComboBox()
        elif c.tipo == "check":
            w = QCheckBox()
            w.setChecked(bool(c.defecto))
        elif c.tipo == "multiline":
            w = QPlainTextEdit()
            w.setFixedHeight(80)
        else:
            w = QLineEdit()
            w.setPlaceholderText(c.placeholder)
        if isinstance(w, (QSpinBox, QDoubleSpinBox)):
            w.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            w.setGroupSeparatorShown(False)
        return w

    def insertar_bajo_formulario(self, widget: QWidget) -> None:
        self._form_layout.insertWidget(self._form_layout.count() - 1, widget)

    def set_opciones(self, campo: str, opciones: Sequence[tuple], conservar: bool = True) -> None:
        w: QComboBox = self._widgets[campo]
        actual = w.currentData()
        w.blockSignals(True)
        w.clear()
        for valor, etiqueta in opciones:
            w.addItem(etiqueta, valor)
        if conservar and actual is not None:
            i = w.findData(actual)
            if i >= 0:
                w.setCurrentIndex(i)
        w.blockSignals(False)

    def widget(self, campo: str) -> QWidget:
        return self._widgets[campo]

    def set_filas(self, filas, ids, colores=None) -> None:
        self.tabla.set_filas(filas, ids, colores)

    @property
    def id_actual(self) -> Optional[int]:
        return self._id

    def set_valores(self, datos: dict, id_: Optional[int]) -> None:
        self._id = id_
        for nombre, w in self._widgets.items():
            if nombre not in datos:
                continue
            v = datos[nombre]
            if isinstance(w, QLineEdit):
                w.setText("" if v is None else str(v))
            elif isinstance(w, QPlainTextEdit):
                w.setPlainText("" if v is None else str(v))
            elif isinstance(w, QSpinBox):
                w.setValue(int(v))
            elif isinstance(w, QDoubleSpinBox):
                w.setValue(float(v))
            elif isinstance(w, QCheckBox):
                w.setChecked(bool(v))
            elif isinstance(w, QComboBox):
                i = w.findData(v)
                w.setCurrentIndex(i if i >= 0 else (0 if w.count() else -1))

    def valores(self) -> dict:
        out: dict = {"id": self._id}
        for nombre, w in self._widgets.items():
            if isinstance(w, QLineEdit):
                out[nombre] = w.text()
            elif isinstance(w, QPlainTextEdit):
                out[nombre] = w.toPlainText()
            elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
                out[nombre] = w.value()
            elif isinstance(w, QCheckBox):
                out[nombre] = w.isChecked()
            elif isinstance(w, QComboBox):
                out[nombre] = w.currentData()
        return out

    def limpiar(self) -> None:
        self._id = None
        self.tabla.clearSelection()
        defectos = {n: (c.defecto if c.defecto is not None else ("" if c.tipo in ("text", "multiline") else 0))
                    for n, c in self._campos.items() if c.tipo != "combo"}
        self.set_valores(defectos, None)

    def _nuevo(self) -> None:
        self.limpiar()
        self.nuevo_solicitado.emit()

    def _eliminar(self) -> None:
        if self._id is not None:
            self.eliminar_solicitado.emit(self._id)
