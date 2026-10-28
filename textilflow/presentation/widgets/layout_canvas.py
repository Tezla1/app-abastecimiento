from typing import Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsTextItem, QGraphicsView, QHBoxLayout,
                             QPushButton, QVBoxLayout, QWidget)

from .. import theme
from ..viewmodels import ArcoVM, NodoVM

ESCALA = 20.0
RADIO = 17.0


class LayoutCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._escena = QGraphicsScene(self)
        self.setScene(self._escena)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setBackgroundBrush(QBrush(QColor(theme.LIENZO)))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._ajustado = True

    def dibujar(self, nodos: Sequence[NodoVM], arcos: Sequence[ArcoVM]) -> None:
        self._escena.clear()
        if not nodos:
            t = self._escena.addText("Sin estaciones registradas en este taller.")
            t.setDefaultTextColor(QColor(theme.TENUE))
            self._escena.setSceneRect(t.boundingRect().adjusted(-40, -40, 40, 40))
            return
        pos = {n.codigo: QPointF(n.x * ESCALA, n.y * ESCALA) for n in nodos}
        self._cuadricula(pos.values())

        for a in arcos:
            if a.origen not in pos or a.destino not in pos:
                continue
            p1, p2 = pos[a.origen], pos[a.destino]
            color = QColor(theme.RESALTE) if a.resaltado else QColor(theme.RUTA)
            self._escena.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(color, 3.5 if a.resaltado else 1.6)).setZValue(1)
            medio = (p1 + p2) / 2
            etiqueta = self._texto(f"{a.distancia_m:g} m", 9, color)
            etiqueta.setPos(medio.x() - etiqueta.boundingRect().width() / 2, medio.y() - 17)
            fondo = self._escena.addRect(etiqueta.pos().x(), etiqueta.pos().y() + 2,
                                         etiqueta.boundingRect().width(), etiqueta.boundingRect().height() - 5,
                                         QPen(Qt.PenStyle.NoPen), QBrush(QColor(theme.LIENZO)))
            fondo.setZValue(2)
            etiqueta.setZValue(3)

        for n in nodos:
            p = pos[n.codigo]
            color = QColor(theme.COLOR_FUNCION.get(n.funcion, theme.AZUL))
            circ = self._escena.addEllipse(p.x() - RADIO, p.y() - RADIO, 2 * RADIO, 2 * RADIO,
                                           QPen(color.lighter(135), 2.5), QBrush(color.darker(180)))
            circ.setZValue(4)
            circ.setToolTip(f"{n.codigo} · {n.nombre}\n({n.x:g}, {n.y:g}) m")
            if n.cerrado:
                circ.setBrush(QBrush(QColor(theme.TRAZO_OFF)))
                circ.setPen(QPen(QColor(theme.ROJO), 3.5))
                circ.setToolTip(f"{n.codigo} · {n.nombre}\nCERRADA")
            cod = self._texto(n.codigo, 10, QColor("white"), negrita=True)
            cod.setPos(p.x() - cod.boundingRect().width() / 2, p.y() - cod.boundingRect().height() / 2)
            cod.setZValue(5)
            nom = self._texto(n.nombre, 9, QColor(theme.TEXTO))
            nom.setPos(p.x() - nom.boundingRect().width() / 2, p.y() + RADIO)
            nom.setZValue(5)

        xs = [q.x() for q in pos.values()]
        ys = [q.y() for q in pos.values()]
        r = QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).adjusted(-70, -60, 70, 60)
        self._escena.setSceneRect(r)
        if self._ajustado:
            self.ajustar()

    def _cuadricula(self, puntos) -> None:
        xs = [p.x() for p in puntos]
        ys = [p.y() for p in puntos]
        x0, x1 = int(min(xs)) - 100, int(max(xs)) + 100
        y0, y1 = int(min(ys)) - 100, int(max(ys)) + 100
        pen = QPen(QColor(theme.CUADRICULA), 1)
        paso = int(5 * ESCALA)
        for x in range(x0 - x0 % paso, x1, paso):
            self._escena.addLine(x, y0, x, y1, pen).setZValue(0)
        for y in range(y0 - y0 % paso, y1, paso):
            self._escena.addLine(x0, y, x1, y, pen).setZValue(0)

    def _texto(self, texto: str, tam: int, color: QColor, negrita: bool = False) -> QGraphicsTextItem:
        t = self._escena.addText(texto)
        f = QFont("Segoe UI", tam)
        f.setBold(negrita)
        t.setFont(f)
        t.setDefaultTextColor(color)
        return t

    def ajustar(self) -> None:
        self._ajustado = True
        if self._escena.items():
            self.fitInView(self._escena.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def acercar(self, factor: float) -> None:
        self._ajustado = False
        self.scale(factor, factor)

    def wheelEvent(self, e) -> None:
        self.acercar(1.15 if e.angleDelta().y() > 0 else 1 / 1.15)

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        if self._ajustado:
            self.ajustar()


class LayoutCanvasConControles(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = LayoutCanvas()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        barra = QHBoxLayout()
        barra.addStretch(1)
        for texto, fn in (("−", lambda: self.canvas.acercar(1 / 1.2)), ("+", lambda: self.canvas.acercar(1.2)),
                          ("Ajustar", self.canvas.ajustar)):
            b = QPushButton(texto)
            b.setFixedWidth(70 if texto == "Ajustar" else 34)
            b.clicked.connect(fn)
            barra.addWidget(b)
        lay.addLayout(barra)
        lay.addWidget(self.canvas, 1)

    def dibujar(self, nodos, arcos) -> None:
        self.canvas.dibujar(nodos, arcos)
