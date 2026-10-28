"""Mapa operativo dinámico: animación de recursos, colas, ocupación y mapa de calor en el tiempo.

La vista solo conoce tuplas planas (viewmodels). Al pulsar un nodo emite `nodo_clicado`.
"""
import bisect
from typing import Optional, Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene,
                             QGraphicsSimpleTextItem, QGraphicsView)

from .. import theme
from ..viewmodels import AnimacionVM, ArcoVM, NodoVM

ESCALA = 22.0
RADIO = 18.0
PASO_MS = 40

# zonas del taller: (clave, título, color)
ZONAS = {
    "ABASTECIMIENTO": ("ABASTECIMIENTO", "#F2A33A"),
    "PROCESO": ("PROCESO", "#2A8FD6"),
    "FLUJO": ("FLUJO INTERNO", "#6F7DF2"),
    "ACABADO": ("ACABADO / EMPAQUE", "#A66BFF"),
    "SALIDA": ("CONTROL / SALIDA", "#1FBFA0"),
}
_PALABRAS_ZONA = [("ACABADO", ("planch", "empaq", "acabad", "etiquet")),
                  ("ABASTECIMIENTO", ("corte", "almac", "abastec", "recep")),
                  ("PROCESO", ("costur", "inspecc", "confecc", "ensambl")),
                  ("FLUJO", ("bordad", "estamp", "lavand", "buffer", "espera")),
                  ("SALIDA", ("despach", "control", "calidad"))]


def zona_de(n) -> str:
    """Zona de un nodo: por función logística y, si es un área de proceso, por palabras de su nombre."""
    if n.funcion == "ALMACEN" or n.funcion == "BASE":
        return "ABASTECIMIENTO"
    if n.funcion == "DESPACHO":
        return "SALIDA"
    if n.funcion == "ESPERA":
        return "FLUJO"
    nombre = n.nombre.lower()
    for z, claves in _PALABRAS_ZONA:
        if any(c in nombre for c in claves):
            return z
    return "PROCESO"


MODOS_CALOR = [
    ("pasadas", "Pasadas por arco (acumulado)"),
    ("kg", "Carga transportada, kg (acumulado)"),
    ("ocupacion", "Ocupación de las áreas (ahora)"),
    ("cola", "Cola en las áreas (ahora)"),
    ("ninguno", "Sin mapa de calor"),
]


class MapaOperativo(QGraphicsView):
    nodo_clicado = pyqtSignal(str)
    tiempo_cambiado = pyqtSignal(float)
    terminado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._escena = QGraphicsScene(self)
        self.setScene(self._escena)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setBackgroundBrush(QBrush(QColor("#0A1426")))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._pos: dict[str, QPointF] = {}
        self._nodos: dict[str, NodoVM] = {}
        self._arcos: dict[frozenset, QGraphicsLineItem] = {}
        self._dist: dict[frozenset, float] = {}
        self._circulos: dict[str, QGraphicsEllipseItem] = {}
        self._badges: dict[str, QGraphicsSimpleTextItem] = {}
        self._resaltes: list = []
        self._recursos_items: list = []
        self._anim: Optional[AnimacionVM] = None
        self._por_recurso: dict[int, list] = {}
        self._inicios_arco: dict[frozenset, list] = {}
        self._inicios_kg: dict[frozenset, list] = {}
        self._max_arco = 1.0
        self._max_kg = 1.0
        self._t = 0.0
        self._velocidad = 20.0   # minutos simulados por segundo real
        self._modo = "pasadas"
        self._seleccion: Optional[str] = None
        self._camino_resaltado: list[tuple] = []
        self._press: Optional[QPointF] = None
        self._timer = QTimer(self)
        self._timer.setInterval(PASO_MS)
        self._timer.timeout.connect(self._tick)
        self._ajustado = True
        self._estatico: dict = {}

    # ------------------------------------------------------------- construcción
    def dibujar(self, nodos: Sequence[NodoVM], arcos: Sequence[ArcoVM]) -> None:
        self.pausar()
        self._escena.clear()
        self._arcos.clear(); self._circulos.clear(); self._badges.clear(); self._dist.clear()
        self._resaltes.clear(); self._recursos_items.clear()
        self._nodos = {n.codigo: n for n in nodos}
        if not nodos:
            t = self._escena.addText("Sin áreas registradas en este taller.")
            t.setDefaultTextColor(QColor(theme.TENUE))
            return
        self._pos = {n.codigo: QPointF(n.x * ESCALA, n.y * ESCALA) for n in nodos}
        self._dibujar_zonas(nodos)
        for a in arcos:
            if a.origen not in self._pos or a.destino not in self._pos:
                continue
            p1, p2 = self._pos[a.origen], self._pos[a.destino]
            it = self._escena.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(QColor("#3A4C70"), 2))
            it.setZValue(1)
            k = frozenset((a.origen, a.destino))
            self._arcos[k] = it
            self._dist[k] = a.distancia_m
            it.setToolTip(f"{a.origen}–{a.destino} · {a.distancia_m:g} m")
            medio = (p1 + p2) / 2
            t = self._escena.addSimpleText(f"{a.distancia_m:g} m")
            t.setFont(QFont("Segoe UI", 8))
            t.setBrush(QBrush(QColor("#6F82A6")))
            t.setPos(medio.x() - t.boundingRect().width() / 2, medio.y() - 16)
            t.setZValue(2)
        for n in nodos:
            p = self._pos[n.codigo]
            color = QColor(theme.COLOR_FUNCION.get(n.funcion, theme.AZUL))
            c = self._escena.addEllipse(p.x() - RADIO, p.y() - RADIO, 2 * RADIO, 2 * RADIO,
                                        QPen(color.lighter(135), 3), QBrush(color.darker(180)))
            c.setZValue(4)
            c.setData(0, n.codigo)
            c.setToolTip(f"{n.codigo} · {n.nombre}\nClic: rutas que pasan por aquí")
            self._circulos[n.codigo] = c
            cod = self._escena.addSimpleText(n.codigo)
            f = QFont("Segoe UI", 10); f.setBold(True)
            cod.setFont(f); cod.setBrush(QBrush(QColor("white")))
            cod.setPos(p.x() - cod.boundingRect().width() / 2, p.y() - cod.boundingRect().height() / 2)
            cod.setZValue(6)
            cod.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            nom = self._escena.addSimpleText(n.nombre)
            nom.setFont(QFont("Segoe UI", 9)); nom.setBrush(QBrush(QColor(theme.TEXTO)))
            nom.setPos(p.x() - nom.boundingRect().width() / 2, p.y() + RADIO + 2)
            nom.setZValue(6)
            nom.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            b = self._escena.addSimpleText("")
            b.setFont(QFont("Segoe UI", 8)); b.setBrush(QBrush(QColor("#FFD166")))
            b.setPos(p.x() - RADIO, p.y() - RADIO - 38)
            b.setZValue(7)
            b.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self._badges[n.codigo] = b
        xs = [q.x() for q in self._pos.values()]; ys = [q.y() for q in self._pos.values()]
        self._escena.setSceneRect(QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).adjusted(-60, -75, 60, 55))
        self.ajustar()
        self._actualizar()

    def _dibujar_zonas(self, nodos) -> None:
        """Recuadros punteados que agrupan las áreas por etapa (abastecimiento, proceso, flujo, acabado, salida)."""
        grupos: dict[str, list] = {}
        for n in nodos:
            grupos.setdefault(zona_de(n), []).append(self._pos[n.codigo])
        for z, pts in grupos.items():
            titulo, col = ZONAS[z]
            c = QColor(col)
            f = QFont("Segoe UI", 8); f.setBold(True)
            t = self._escena.addSimpleText(titulo)
            t.setFont(f); t.setBrush(QBrush(c.lighter(115)))
            x0 = min(q.x() for q in pts) - RADIO - 14; x1 = max(q.x() for q in pts) + RADIO + 14
            ancho_t = t.boundingRect().width() + 12
            if x1 - x0 < ancho_t:                      # zona de un solo nodo: ancho mínimo para el título
                m = (x0 + x1) / 2; x0, x1 = m - ancho_t / 2, m + ancho_t / 2
            y0 = min(q.y() for q in pts) - RADIO - 8; y1 = max(q.y() for q in pts) + RADIO + 22
            relleno = QColor(c); relleno.setAlpha(24)
            borde = QPen(QColor(c.red(), c.green(), c.blue(), 150), 1.4, Qt.PenStyle.DashLine)
            r = self._escena.addRect(QRectF(x0, y0, x1 - x0, y1 - y0), borde, QBrush(relleno))
            r.setZValue(0)
            r.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            t.setPos(x0 + 6, y1 + 1)                   # título bajo el recuadro: no tapa nombres ni códigos
            t.setZValue(0.5)
            t.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    # ------------------------------------------------------------- datos de animación
    def cargar_animacion(self, anim: Optional[AnimacionVM]) -> None:
        self.pausar()
        for it in self._recursos_items:
            self._escena.removeItem(it)
        self._recursos_items.clear()
        self._anim = anim
        self._por_recurso.clear(); self._inicios_arco.clear(); self._inicios_kg.clear()
        self._t = 0.0
        if anim:
            for m in sorted(anim.movimientos, key=lambda m: m[1]):
                self._por_recurso.setdefault(m[0], []).append(m)
                for a, b in zip(m[3], m[3][1:]):
                    k = frozenset((a, b))
                    self._inicios_arco.setdefault(k, []).append(m[1])
                    self._inicios_kg.setdefault(k, []).append((m[1], m[5]))
            self._max_arco = max((len(v) for v in self._inicios_arco.values()), default=1)
            self._max_kg = max((sum(kg for _, kg in v) for v in self._inicios_kg.values()), default=1.0) or 1.0
            for r in range(1, anim.recursos + 1):
                color = QColor(theme.COLOR_RECURSOS[(r - 1) % len(theme.COLOR_RECURSOS)])
                it = QGraphicsRectItem(-8, -8, 16, 16)
                it.setBrush(QBrush(color)); it.setPen(QPen(QColor("white"), 1.5)); it.setZValue(9)
                it.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                lab = QGraphicsSimpleTextItem(str(r), it)
                lab.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold)); lab.setBrush(QBrush(QColor("#0B1220")))
                lab.setPos(-lab.boundingRect().width() / 2, -lab.boundingRect().height() / 2)
                kg = QGraphicsSimpleTextItem("", it)
                kg.setFont(QFont("Segoe UI", 8)); kg.setBrush(QBrush(QColor("#FFD166"))); kg.setPos(10, -18)
                self._escena.addItem(it)
                self._recursos_items.append((it, kg, r))
        self._actualizar()

    def calor_estatico(self, trafico: dict) -> None:
        """Mapa de calor fijo (sin animación): {frozenset({a, b}): pasadas}."""
        self._estatico = dict(trafico)
        self._actualizar()

    # ------------------------------------------------------------- reproducción
    def reproducir(self) -> None:
        if not self._anim:
            return
        if self._t >= self._anim.t_fin:
            self.set_tiempo(0.0)
        self._timer.start()

    def pausar(self) -> None:
        self._timer.stop()

    @property
    def reproduciendo(self) -> bool:
        return self._timer.isActive()

    def set_velocidad(self, min_por_s: float) -> None:
        self._velocidad = max(0.01, float(min_por_s))

    def set_modo_calor(self, modo: str) -> None:
        self._modo = modo
        self._actualizar()

    def set_tiempo(self, t: float) -> None:
        self._t = max(0.0, min(t, self._anim.t_fin if self._anim else 0.0))
        self._actualizar()
        self.tiempo_cambiado.emit(self._t)

    @property
    def tiempo(self) -> float:
        return self._t

    def _tick(self) -> None:
        if not self._anim:
            self.pausar()
            return
        nuevo = self._t + self._velocidad * PASO_MS / 1000.0
        if nuevo >= self._anim.t_fin:
            self.set_tiempo(self._anim.t_fin)
            self.pausar()
            self.terminado.emit()
            return
        self.set_tiempo(nuevo)

    # ------------------------------------------------------------- selección y rutas resaltadas
    def resaltar_caminos(self, caminos: Sequence[tuple], principal: Optional[int] = 0, nodo: Optional[str] = None) -> None:
        """Dibuja encima los caminos (tuplas de nodos). El índice `principal` se resalta más."""
        for it in self._resaltes:
            self._escena.removeItem(it)
        self._resaltes.clear()
        self._seleccion = nodo
        for i, camino in enumerate(caminos):
            es_principal = i == principal
            pen = QPen(QColor("#FFD166" if es_principal else "#FF9F6B"), 5 if es_principal else 3)
            pen.setStyle(Qt.PenStyle.SolidLine if es_principal else Qt.PenStyle.DashLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            for a, b in zip(camino, camino[1:]):
                if a in self._pos and b in self._pos:
                    it = self._escena.addLine(self._pos[a].x(), self._pos[a].y(), self._pos[b].x(), self._pos[b].y(), pen)
                    it.setZValue(3 if es_principal else 2.5)
                    it.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                    self._resaltes.append(it)
        self._actualizar()

    def limpiar_resaltes(self) -> None:
        self.resaltar_caminos([], None, None)

    # ------------------------------------------------------------- actualización por instante
    def _actualizar(self) -> None:
        t = self._t
        a = self._anim
        # --- arcos (mapa de calor)
        for k, it in self._arcos.items():
            if a and self._modo == "pasadas":
                n = bisect.bisect_right(self._inicios_arco.get(k, []), t)
                x = n / self._max_arco
            elif not a and self._estatico:
                x = self._estatico.get(k, 0) / (max(self._estatico.values()) or 1)
            elif a and self._modo == "kg":
                lst = self._inicios_kg.get(k, [])
                x = sum(kg for tt, kg in lst if tt <= t) / self._max_kg
            else:
                x = None
            if x is None:
                it.setPen(QPen(QColor("#3A4C70"), 2))
            else:
                it.setPen(QPen(QColor(theme.color_calor(x) if x > 0 else "#2A3A5C"), 2 + 7 * x, Qt.PenStyle.SolidLine,
                               Qt.PenCapStyle.RoundCap))
        # --- nodos: ocupación / cola
        ocup, cola = {}, {}
        if a:
            for est, lleg, ini, fin in a.visitas:
                if lleg <= t and (ini is None or ini > t):
                    cola[est] = cola.get(est, 0) + 1
                elif ini is not None and ini <= t < (fin if fin is not None else 1e18):
                    ocup[est] = ocup.get(est, 0) + 1
        for cod, c in self._circulos.items():
            n = self._nodos[cod]
            base = QColor(theme.COLOR_FUNCION.get(n.funcion, theme.AZUL))
            cap = a.capacidad.get(cod, 0) if a else 0
            relleno, borde = base.darker(180), base.lighter(135)
            if a and cap:
                if self._modo == "ocupacion":
                    relleno = QColor(theme.color_calor(ocup.get(cod, 0) / cap)).darker(115)
                elif self._modo == "cola":
                    relleno = QColor(theme.color_calor(min(cola.get(cod, 0) / 6.0, 1.0))).darker(115)
                if ocup.get(cod, 0):
                    borde = QColor(theme.VERDE)
            seleccionado = cod == self._seleccion
            c.setBrush(QBrush(relleno))
            c.setPen(QPen(QColor("#FFD166") if seleccionado else borde, 4 if seleccionado else 3))
            q, o = cola.get(cod, 0), ocup.get(cod, 0)
            self._badges[cod].setText((f"cola {q}" if q else "") + (" · " if q and o else "") + (f"▶{o}/{cap}" if o and cap else ""))
        # --- recursos
        for it, kg, r in self._recursos_items:
            pos, carga = self._pos_recurso(r, t)
            if pos is None:
                it.setVisible(False)
                continue
            it.setVisible(True)
            # parado en un área: se dibuja SOBRE el círculo (no dentro), uno al lado del otro
            for cod, q in self._pos.items():
                if abs(q.x() - pos.x()) < 0.5 and abs(q.y() - pos.y()) < 0.5:
                    n = len(self._recursos_items)
                    pos = QPointF(q.x() + (r - 1 - (n - 1) / 2) * 22, q.y() - RADIO - 14)
                    break
            it.setPos(pos)
            it.setOpacity(1.0 if carga > 0 else 0.55)
            kg.setText(f"{carga:g} kg" if carga > 0 else "")

    def _pos_recurso(self, r: int, t: float):
        movs = self._por_recurso.get(r, [])
        a = self._anim
        if not movs:
            return (self._pos.get(a.inicio) if a else None), 0.0
        idx = bisect.bisect_right([m[1] for m in movs], t) - 1
        if idx < 0:
            return self._pos.get(a.inicio), 0.0
        _, t0, t1, ruta, cargado, kg = movs[idx]
        if t >= t1 or t1 <= t0:
            return self._pos.get(ruta[-1]), 0.0
        pts = [self._pos[n] for n in ruta if n in self._pos]
        if len(pts) < 2:
            return (pts[0] if pts else None), kg if cargado else 0.0
        tramos = [(pts[i], pts[i + 1], ((pts[i + 1].x() - pts[i].x()) ** 2 + (pts[i + 1].y() - pts[i].y()) ** 2) ** 0.5)
                  for i in range(len(pts) - 1)]
        total = sum(d for _, _, d in tramos) or 1.0
        objetivo = (t - t0) / (t1 - t0) * total
        for p1, p2, d in tramos:
            if objetivo <= d or d == 0:
                f = objetivo / d if d else 0.0
                return QPointF(p1.x() + (p2.x() - p1.x()) * f, p1.y() + (p2.y() - p1.y()) * f), (kg if cargado else 0.0)
            objetivo -= d
        return pts[-1], kg if cargado else 0.0

    # ------------------------------------------------------------- interacción y zoom
    def mousePressEvent(self, e) -> None:
        self._press = e.position()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e) -> None:
        super().mouseReleaseEvent(e)
        if self._press is not None and (e.position() - self._press).manhattanLength() < 5:
            for it in self.items(e.position().toPoint()):
                cod = it.data(0)
                if cod:
                    self.nodo_clicado.emit(str(cod))
                    break
        self._press = None

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
