"""Filas que pasan a columna cuando la ventana es demasiado angosta para ponerlas lado a lado."""
import weakref
from typing import Optional

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtWidgets import QBoxLayout, QLayout, QWidget

_MAX = 16777215       # QWIDGETSIZE_MAX


class FilaAdaptable(QBoxLayout):
    """Como un QHBoxLayout, pero si el ancho disponible no alcanza para el mínimo de sus elementos en fila,
    los apila en vertical. Así en pantallas chicas no hace falta desplazarse hacia los lados."""

    _todas: "weakref.WeakSet" = weakref.WeakSet()
    _ancho = 100000                                   # ancho disponible conocido (la ventana lo actualiza)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(QBoxLayout.Direction.LeftToRight, parent)
        self._fijos: list = []
        FilaAdaptable._todas.add(self)

    def fijar_ancho(self, widget: QWidget, ancho: int) -> None:
        """Ancho fijo del widget en modo fila; en modo columna se libera para que use todo el ancho."""
        self._fijos.append((widget, ancho))
        widget.setFixedWidth(ancho)

    def _minimo_en_fila(self) -> int:
        n, total = self.count(), 0
        for i in range(n):
            it = self.itemAt(i)
            if it is not None and it.widget() is not None and it.widget().isHidden():
                continue
            total += it.minimumSize().width() if it is not None else 0
        return total + max(n - 1, 0) * self.spacing() + self.contentsMargins().left() + self.contentsMargins().right()

    def evaluar(self) -> None:
        angosto = self._minimo_en_fila() > FilaAdaptable._ancho
        nueva = QBoxLayout.Direction.TopToBottom if angosto else QBoxLayout.Direction.LeftToRight
        if self.direction() == nueva:
            return
        self.setDirection(nueva)
        for w, ancho in self._fijos:
            if angosto:
                w.setMinimumWidth(0)
                w.setMaximumWidth(_MAX)
            else:
                w.setFixedWidth(ancho)
        self.invalidate()
        self._avisar_al_padre()

    def _avisar_al_padre(self) -> None:
        # los tamaños mínimos quedan en caché en los contenedores (pestañas ocultas incluidas): se les avisa del cambio
        w = self.parentWidget()
        while w is not None and w.objectName() != "pagina":
            w.updateGeometry()
            if w.layout() is not None:
                w.layout().invalidate()
            w = w.parentWidget()
        if w is not None:
            w.updateGeometry()
            if w.layout() is not None:
                w.layout().invalidate()

    def minimumSize(self):
        # Qt lo consulta al calcular el tamaño de la página, cuando ya están todos los elementos cargados
        self.evaluar()
        return super().minimumSize()

    def sizeHint(self):
        self.evaluar()
        return super().sizeHint()

    def addWidget(self, *a, **k):
        super().addWidget(*a, **k)
        self.evaluar()

    def addLayout(self, *a, **k):
        super().addLayout(*a, **k)
        self.evaluar()

    @classmethod
    def actualizar(cls, ancho_disponible: int) -> None:
        """La ventana avisa cuánto ancho útil tienen las páginas; cada fila decide si cabe en horizontal."""
        cls._ancho = ancho_disponible
        for fila in list(cls._todas):
            try:
                fila.evaluar()
            except RuntimeError:                      # la fila ya fue destruida
                pass


class FlujoLayout(QLayout):
    """Reparte sus elementos en filas y salta a la siguiente cuando no caben (tarjetas de indicadores, barras de herramientas).

    Su ancho mínimo es el del elemento más ancho, así la página puede achicarse sin desplazamiento horizontal.
    """

    def __init__(self, parent: Optional[QWidget] = None, margen: int = 0, espacio: int = 8):
        super().__init__(parent)
        self._items: list = []
        self._espacio = espacio
        self.setContentsMargins(margen, margen, margen, margen)

    def addItem(self, item) -> None:
        self._items.append(item)
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, i: int):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i: int):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, ancho: int) -> int:
        return self._distribuir(QRect(0, 0, ancho, 0), solo_medir=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._distribuir(rect, solo_medir=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        w = max((i.minimumSize().width() for i in self._items), default=0)
        h = max((i.minimumSize().height() for i in self._items), default=0)
        m = self.contentsMargins()
        return QSize(w + m.left() + m.right(), h + m.top() + m.bottom())

    def _distribuir(self, rect: QRect, solo_medir: bool) -> int:
        m = self.contentsMargins()
        r = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, alto_fila = r.x(), r.y(), 0
        visibles = [i for i in self._items if not (i.widget() is not None and i.widget().isHidden())]
        fila: list = []

        def cerrar_fila() -> None:
            # los elementos de la fila se reparten el ancho sobrante en partes iguales (como tarjetas del mismo tamaño)
            nonlocal x, y, alto_fila, fila
            if not fila:
                return
            if not solo_medir:
                libre = r.width() - (len(fila) - 1) * self._espacio
                ancho_base = libre // len(fila)
                xx = r.x()
                for it in fila:
                    ancho = max(it.minimumSize().width(), min(ancho_base, it.maximumSize().width()))
                    it.setGeometry(QRect(xx, y, ancho, alto_fila))
                    xx += ancho + self._espacio
            y += alto_fila + self._espacio
            x, alto_fila, fila = r.x(), 0, []

        for it in visibles:
            w = it.sizeHint().width()
            if fila and x + w > r.right() + 1:
                cerrar_fila()
            fila.append(it)
            x += w + self._espacio
            alto_fila = max(alto_fila, it.sizeHint().height())
        cerrar_fila()
        return y - self._espacio + m.bottom() - rect.y() if visibles else m.top() + m.bottom()
