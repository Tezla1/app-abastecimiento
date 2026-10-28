from typing import Optional, Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QAbstractItemView, QFrame, QHeaderView, QLabel, QMessageBox,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .. import theme


def _es_numero(valor) -> bool:
    try:
        float(str(valor).replace(",", "").rstrip("%"))
        return True
    except ValueError:
        return False


class KpiCard(QFrame):
    def __init__(self, titulo: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setStyleSheet(f"QFrame#tarjeta {{ background: {color}; border: none; border-radius: 10px; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)
        self._titulo = QLabel(titulo)
        self._titulo.setStyleSheet("font-weight: 600; color: rgba(255,255,255,0.85);")
        self._valor = QLabel("—")
        self._valor.setStyleSheet("font-size: 24px; font-weight: 700;")
        self._nota = QLabel("")
        self._nota.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px;")
        for w in (self._titulo, self._valor, self._nota):
            lay.addWidget(w)

    def set_valor(self, valor: str, nota: str = "") -> None:
        self._valor.setText(valor)
        self._nota.setText(nota)


class DataTable(QTableWidget):
    fila_seleccionada = pyqtSignal(object)

    def __init__(self, encabezados: Sequence[str], parent=None, estirar: Optional[int] = None):
        super().__init__(0, len(encabezados), parent)
        self.setHorizontalHeaderLabels(list(encabezados))
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(estirar is None)
        if estirar is not None:
            self.horizontalHeader().setSectionResizeMode(estirar, QHeaderView.ResizeMode.Stretch)
        self.itemSelectionChanged.connect(self._emitir)
        self._ajustar_filas = False

    def texto_largo(self, columnas: Sequence[int], pesos: Optional[Sequence[float]] = None) -> None:
        """Columnas con texto largo: se reparten el ancho y el texto baja de renglón en vez de cortarse.

        Con `pesos` el reparto no es parejo: la columna con más texto recibe más ancho (filas menos altas)."""
        self._pesos = dict(zip(columnas, pesos)) if pesos else {}
        for c in columnas:
            self.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.Interactive if self._pesos else QHeaderView.ResizeMode.Stretch)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self._ajustar_filas = True

    def _repartir_ancho(self) -> None:
        pesos = getattr(self, "_pesos", None)
        if not pesos:
            return
        cab = self.horizontalHeader()
        fijo = sum(cab.sectionSize(c) for c in range(self.columnCount()) if c not in pesos)
        libre = max(self.viewport().width() - fijo, 120 * len(pesos))
        total = sum(pesos.values())
        for c, p in pesos.items():
            cab.resizeSection(c, int(libre * p / total))

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._repartir_ancho()
        if self._ajustar_filas:
            self.resizeRowsToContents()

    def set_filas(self, filas: Sequence[Sequence], ids: Optional[Sequence] = None,
                  colores: Optional[Sequence[Optional[str]]] = None) -> None:
        self.blockSignals(True)
        self.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                item = QTableWidgetItem("" if valor is None else str(valor))
                numerico = j > 0 and _es_numero(valor)
                if numerico:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if j == 0 and ids is not None:
                    item.setData(Qt.ItemDataRole.UserRole, ids[i])
                if colores and colores[i] and j == 0:
                    item.setForeground(QColor(colores[i]))
                if self._ajustar_filas and isinstance(valor, str) and len(valor) > 40:
                    item.setToolTip(valor)
                self.setItem(i, j, item)
        self.blockSignals(False)
        self._repartir_ancho()
        if self._ajustar_filas:
            self.resizeRowsToContents()
        self.clearSelection()

    def id_seleccionado(self):
        filas = self.selectionModel().selectedRows()
        if not filas:
            return None
        return self.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def seleccionar_id(self, id_) -> None:
        for i in range(self.rowCount()):
            if self.item(i, 0).data(Qt.ItemDataRole.UserRole) == id_:
                self.selectRow(i)
                return

    def _emitir(self) -> None:
        self.fila_seleccionada.emit(self.id_seleccionado())


class PageView(QWidget):

    def __init__(self, titulo: str, subtitulo: str, acento: str, parent=None):
        super().__init__(parent)
        self.setObjectName("pagina")
        self.acento = acento
        self._raiz = QVBoxLayout(self)
        self._raiz.setContentsMargins(24, 18, 24, 18)
        self._raiz.setSpacing(10)
        t = QLabel(titulo)
        t.setObjectName("titulo")
        s = QLabel(subtitulo)
        s.setObjectName("subtitulo")
        s.setWordWrap(True)
        linea = QFrame()
        linea.setFixedHeight(2)
        linea.setStyleSheet(f"background: {acento};")
        for w in (t, s, linea):
            self._raiz.addWidget(w)
        self.estado = QLabel("")
        self.estado.setObjectName("estado")
        self.estado.setWordWrap(True)

    @property
    def cuerpo(self) -> QVBoxLayout:
        return self._raiz

    def error(self, mensaje: str) -> None:
        QMessageBox.warning(self, "TextilFlow", mensaje)

    def info(self, mensaje: str) -> None:
        self.estado.setText(mensaje)

    def confirmar(self, mensaje: str) -> bool:
        r = QMessageBox.question(self, "TextilFlow", mensaje,
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No)
        return r == QMessageBox.StandardButton.Yes
