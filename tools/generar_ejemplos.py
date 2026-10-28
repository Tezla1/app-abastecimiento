"""Genera los ejemplos .xlsx difíciles de la carpeta `ejemplos/` (datos sintéticos, reproducibles).

Uso:  python tools/generar_ejemplos.py
"""
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from textilflow.domain.entities import Conexion, Estacion, Pedido, RutaProceso, Taller, TipoPrenda   # noqa: E402
from textilflow.infrastructure.excel.openpyxl_gateway import OpenpyxlGateway                         # noqa: E402


class Caso:
    def __init__(self, nombre, area, operadores, obs):
        self.taller = Taller(nombre, area, operadores, 8.0, "SINTETICO", obs)
        self.est, self.con, self.tipos, self.rutas, self.pedidos = [], [], [], [], []
        self._pos = {}
        self.escala = 1.0

    def n(self, cod, nombre, func, x, y, t=0.0, cap=1, grupo=""):
        self.est.append(Estacion(1, cod, nombre, func, x, y, t, cap, grupo))
        self._pos[cod] = (x, y)

    def e(self, *pares, ancho=1.8):
        """Conexiones bidireccionales; la distancia sale de las coordenadas (múltiplos de 0,5 m)."""
        for a, b in pares:
            (x1, y1), (x2, y2) = self._pos[a], self._pos[b]
            d = max(3.0, round(math.hypot(x2 - x1, y2 - y1) * 2) / 2)
            self.con.append(Conexion(1, a, b, d, ancho))

    def prenda(self, nombre, kg, lote, factor=1.0):
        self.tipos.append(TipoPrenda(nombre, kg, lote, factor, id=len(self.tipos) + 1))

    def ruta(self, prenda, nombre, pct, seq):
        pid = next(t.id for t in self.tipos if t.nombre == prenda)
        self.rutas.append(RutaProceso(1, pid, nombre, pct, seq))

    def pedido(self, prenda, cant, prio, llegada, venc=0):
        cant = max(1, round(cant * self.escala))
        pid = next(t.id for t in self.tipos if t.nombre == prenda)
        self.pedidos.append(Pedido(1, pid, cant, prio, llegada, venc))

    def guardar(self, archivo):
        OpenpyxlGateway().escribir_taller(str(RAIZ / "ejemplos" / archivo), self.taller, self.est, self.con,
                                          self.tipos, self.rutas, self.pedidos)


# ----------------------------------------------------------------------------------------------- DIFÍCIL
def dificil():
    c = Caso("Ejemplo 03 - DIFÍCIL · Camisería y pantalonería (14 áreas)", 600, 30,
             "Dos cuellos de botella (Bordado y Estampado), 3 costuras alternativas y 5 prendas.")
    c.escala = 0.85
    c.n("A", "Almacén", "ALMACEN", 2, 10)
    c.n("T", "Tendido", "PROCESO", 8, 10, 0.3, 2)
    c.n("C", "Corte", "PROCESO", 14, 10, 0.6, 3)
    c.n("ES", "Estampado", "PROCESO", 20, 3, 1.2, 1)
    c.n("B", "Bordado", "PROCESO", 20, 17, 1.4, 1)
    c.n("S1", "Costura A", "PROCESO", 26, 5, 2.3, 4, "COSTURA")
    c.n("S2", "Costura B", "PROCESO", 26, 10, 2.3, 4, "COSTURA")
    c.n("S3", "Costura C", "PROCESO", 26, 15, 2.3, 4, "COSTURA")
    c.n("OJ", "Ojales y botones", "PROCESO", 32, 7, 0.5, 2)
    c.n("I", "Inspección", "PROCESO", 32, 13, 0.4, 2)
    c.n("P", "Planchado", "PROCESO", 38, 10, 0.7, 2)
    c.n("PL", "Plegado", "PROCESO", 44, 5, 0.3, 2)
    c.n("E", "Empaque", "PROCESO", 44, 15, 0.5, 2)
    c.n("D", "Despacho", "DESPACHO", 50, 10)
    c.e(("A", "T"), ("T", "C"), ("C", "ES"), ("C", "B"), ("C", "S2"), ("ES", "S1"), ("B", "S3"), ("S1", "S2"),
        ("S2", "S3"), ("S1", "OJ"), ("S2", "OJ"), ("S2", "I"), ("S3", "I"), ("OJ", "I"), ("OJ", "P"), ("I", "P"),
        ("P", "PL"), ("P", "E"), ("PL", "E"), ("PL", "D"), ("E", "D"))
    c.e(("C", "S1"), ("C", "S3"), ancho=1.1)           # atajos angostos (alertas normativas)
    c.prenda("Camisa Formal", 0.25, 24, 1.0)
    c.prenda("Pantalón Sastre", 0.60, 20, 1.2)
    c.prenda("Blusa", 0.20, 30, 0.9)
    c.prenda("Polo", 0.22, 30, 0.8)
    c.prenda("Bermuda", 0.40, 24, 1.0)
    c.ruta("Camisa Formal", "Lisa", 50, "A>T>C>@COSTURA>OJ>I>P>PL>E>D")
    c.ruta("Camisa Formal", "Bordada", 30, "A>T>C>B>@COSTURA>OJ>I>P>E>D")
    c.ruta("Camisa Formal", "Estampada", 20, "A>T>C>ES>@COSTURA>OJ>I>P>PL>E>D")
    c.ruta("Pantalón Sastre", "Estándar", 70, "A>T>C>@COSTURA>OJ>P>E>D")
    c.ruta("Pantalón Sastre", "Con inspección", 30, "A>T>C>@COSTURA>I>OJ>P>PL>E>D")
    c.ruta("Blusa", "Bordada", 60, "A>T>C>B>@COSTURA>I>P>E>D")
    c.ruta("Blusa", "Lisa", 40, "A>T>C>@COSTURA>I>PL>E>D")
    c.ruta("Polo", "Estampado", 70, "A>T>C>ES>@COSTURA>PL>E>D")
    c.ruta("Polo", "Liso", 30, "A>T>C>@COSTURA>PL>E>D")
    c.ruta("Bermuda", "Única", 100, "A>T>C>@COSTURA>OJ>P>E>D")
    for p in [("Camisa Formal", 360, 3, 0, 440), ("Pantalón Sastre", 240, 2, 20, 360), ("Blusa", 300, 3, 40, 0),
              ("Polo", 420, 4, 60, 0), ("Bermuda", 200, 3, 80, 460), ("Camisa Formal", 180, 1, 120, 300),
              ("Blusa", 150, 2, 150, 420), ("Polo", 240, 4, 200, 0)]:
        c.pedido(*p)
    return c


# ------------------------------------------------------------------------------------------ MUY DIFÍCIL
def muy_dificil():
    c = Caso("Ejemplo 04 - MUY DIFÍCIL · Planta de denim con lavandería (20 áreas)", 1100, 55,
             "Lavandería como cuello de botella, retrabajo de calidad, buffer, tres grupos paralelos y pasillos estrechos.")
    c.escala = 0.7
    c.n("A", "Almacén", "ALMACEN", 2, 12)
    c.n("RC", "Recepción y conteo", "PROCESO", 8, 12, 0.15, 2)
    c.n("T", "Tendido", "PROCESO", 14, 12, 0.3, 2)
    c.n("C1", "Corte A", "PROCESO", 20, 7, 0.7, 2, "CORTE")
    c.n("C2", "Corte B", "PROCESO", 20, 17, 0.7, 2, "CORTE")
    c.n("BF", "Buffer de piezas", "ESPERA", 26, 12)
    c.n("S1", "Costura 1", "PROCESO", 32, 4, 2.6, 4, "COSTURA")
    c.n("S2", "Costura 2", "PROCESO", 32, 10, 2.6, 4, "COSTURA")
    c.n("S3", "Costura 3", "PROCESO", 32, 16, 2.6, 4, "COSTURA")
    c.n("S4", "Costura 4", "PROCESO", 32, 22, 2.6, 4, "COSTURA")
    c.n("BO", "Bordado", "PROCESO", 38, 24, 1.6, 2)
    c.n("LV", "Lavandería", "PROCESO", 40, 14, 1.2, 3)
    c.n("SE", "Secado", "PROCESO", 46, 14, 0.6, 2)
    c.n("I", "Inspección", "PROCESO", 52, 8, 0.5, 2)
    c.n("RT", "Retrabajo", "PROCESO", 52, 20, 1.5, 2)
    c.n("P1", "Planchado 1", "PROCESO", 58, 6, 0.8, 2, "PLANCHADO")
    c.n("P2", "Planchado 2", "PROCESO", 58, 12, 0.8, 2, "PLANCHADO")
    c.n("E", "Empaque", "PROCESO", 64, 9, 0.6, 3)
    c.n("ET", "Etiquetado", "PROCESO", 64, 17, 0.3, 2)
    c.n("D", "Despacho", "DESPACHO", 72, 12)
    c.e(("A", "RC"), ("RC", "T"), ("T", "C1"), ("T", "C2"), ("C1", "BF"), ("C2", "BF"), ("BF", "S1"), ("BF", "S2"),
        ("BF", "S3"), ("BF", "S4"), ("S1", "S2"), ("S2", "S3"), ("S3", "S4"), ("S2", "LV"), ("S3", "LV"),
        ("S4", "BO"), ("BO", "LV"), ("LV", "SE"), ("SE", "I"), ("SE", "RT"), ("I", "RT"), ("I", "P1"), ("I", "P2"),
        ("SE", "P2"), ("P1", "E"), ("P2", "E"), ("P2", "ET"), ("E", "ET"), ("E", "D"), ("ET", "D"), ("RT", "ET"))
    c.e(("S1", "LV"), ("S4", "LV"), ("C1", "C2"), ancho=1.0)    # pasillos angostos
    c.prenda("Jean", 0.80, 15, 1.0)
    c.prenda("Chaqueta Denim", 1.10, 10, 1.6)
    c.prenda("Vestido", 0.35, 20, 1.2)
    c.prenda("Falda", 0.30, 24, 0.9)
    c.prenda("Overol", 1.20, 10, 1.9)
    c.prenda("Short", 0.35, 30, 0.8)
    c.prenda("Buzo", 0.55, 20, 1.1)
    c.ruta("Jean", "Lavado clásico", 55, "A>RC>T>@CORTE>BF>@COSTURA>LV>SE>I>@PLANCHADO>E>D")
    c.ruta("Jean", "Bordado de bolsillo", 25, "A>RC>T>@CORTE>BF>@COSTURA>BO>LV>SE>I>@PLANCHADO>E>ET>D")
    c.ruta("Jean", "Con retrabajo", 20, "A>RC>T>@CORTE>BF>@COSTURA>LV>SE>I>RT>I>@PLANCHADO>E>D")
    c.ruta("Chaqueta Denim", "Lavada", 60, "A>RC>T>@CORTE>BF>@COSTURA>LV>SE>I>@PLANCHADO>E>ET>D")
    c.ruta("Chaqueta Denim", "Bordada", 40, "A>RC>T>@CORTE>BF>@COSTURA>BO>LV>SE>RT>I>@PLANCHADO>E>ET>D")
    c.ruta("Vestido", "Estándar", 70, "A>RC>T>@CORTE>BF>@COSTURA>I>@PLANCHADO>ET>D")
    c.ruta("Vestido", "Con bordado", 30, "A>RC>T>@CORTE>BF>@COSTURA>BO>I>@PLANCHADO>ET>D")
    c.ruta("Falda", "Estándar", 80, "A>RC>T>@CORTE>BF>@COSTURA>@PLANCHADO>E>D")
    c.ruta("Falda", "Con inspección", 20, "A>RC>T>@CORTE>BF>@COSTURA>I>@PLANCHADO>E>D")
    c.ruta("Overol", "Lavado industrial", 100, "A>RC>T>@CORTE>BF>@COSTURA>LV>SE>I>RT>I>E>ET>D")
    c.ruta("Short", "Lavado suave", 60, "A>RC>T>@CORTE>BF>@COSTURA>LV>SE>@PLANCHADO>E>D")
    c.ruta("Short", "Sin lavado", 40, "A>RC>T>@CORTE>BF>@COSTURA>@PLANCHADO>E>D")
    c.ruta("Buzo", "Estándar", 100, "A>RC>T>@CORTE>BF>@COSTURA>BO>@PLANCHADO>ET>D")
    for p in [("Jean", 450, 3, 0, 460), ("Chaqueta Denim", 200, 2, 15, 400), ("Vestido", 300, 3, 30, 0),
              ("Falda", 360, 4, 45, 0), ("Overol", 120, 1, 60, 330), ("Short", 420, 3, 90, 470),
              ("Buzo", 240, 3, 110, 0), ("Jean", 300, 2, 140, 480), ("Chaqueta Denim", 150, 1, 170, 400),
              ("Vestido", 180, 4, 210, 0), ("Short", 240, 3, 240, 0), ("Overol", 80, 1, 280, 440)]:
        c.pedido(*p)
    return c


# ------------------------------------------------------------------------------------------------ ULTRA
def ultra():
    c = Caso("Ejemplo 05 - ULTRA · Planta integral de 3 naves (29 áreas)", 2600, 120,
             "Tres naves unidas por un solo pasillo, varias áreas con carga >100 %, 10 prendas, 20 pedidos con plazos ajustados.")
    c.escala = 0.7
    # nave 1: recepción y corte
    c.n("A", "Almacén", "ALMACEN", 2, 16)
    c.n("RC", "Recepción", "PROCESO", 8, 16, 0.12, 3)
    c.n("RV", "Revisión de tela", "PROCESO", 14, 16, 0.2, 2)
    c.n("T", "Tendido", "PROCESO", 20, 16, 0.3, 2)
    c.n("C1", "Corte A", "PROCESO", 26, 9, 0.7, 2, "CORTE")
    c.n("C2", "Corte B", "PROCESO", 26, 16, 0.7, 2, "CORTE")
    c.n("C3", "Corte C", "PROCESO", 26, 23, 0.7, 2, "CORTE")
    c.n("BF", "Buffer de piezas", "ESPERA", 32, 16)
    c.n("PA", "Pasillo central", "ESPERA", 38, 16)            # único enlace entre naves (nodo crítico)
    # nave 2: confección
    c.n("S1", "Costura 1", "PROCESO", 44, 4, 2.5, 4, "COSTURA")
    c.n("S2", "Costura 2", "PROCESO", 44, 10, 2.5, 4, "COSTURA")
    c.n("S3", "Costura 3", "PROCESO", 44, 16, 2.5, 4, "COSTURA")
    c.n("S4", "Costura 4", "PROCESO", 44, 22, 2.5, 4, "COSTURA")
    c.n("S5", "Costura 5", "PROCESO", 44, 28, 2.5, 4, "COSTURA")
    c.n("OJ", "Ojales y botones", "PROCESO", 50, 7, 0.6, 2)
    c.n("BO", "Bordado", "PROCESO", 50, 25, 1.7, 2)
    c.n("ES", "Estampado", "PROCESO", 50, 19, 1.3, 2)
    c.n("TE", "Termofijado", "PROCESO", 50, 13, 0.9, 2)
    # nave 3: acabado
    c.n("LV", "Lavandería", "PROCESO", 58, 16, 2.0, 3)
    c.n("SE", "Secado", "PROCESO", 64, 16, 0.6, 2)
    c.n("I", "Inspección", "PROCESO", 70, 9, 0.5, 2)
    c.n("RT", "Retrabajo", "PROCESO", 70, 23, 1.4, 1)
    c.n("P1", "Planchado 1", "PROCESO", 76, 6, 0.8, 2, "PLANCHADO")
    c.n("P2", "Planchado 2", "PROCESO", 76, 14, 0.8, 2, "PLANCHADO")
    c.n("P3", "Planchado 3", "PROCESO", 76, 22, 0.8, 2, "PLANCHADO")
    c.n("PL", "Plegado", "PROCESO", 82, 10, 0.3, 3)
    c.n("E", "Empaque", "PROCESO", 82, 18, 0.6, 3)
    c.n("ET", "Etiquetado", "PROCESO", 88, 14, 0.3, 2)
    c.n("D", "Despacho", "DESPACHO", 96, 14)
    c.e(("A", "RC"), ("RC", "RV"), ("RV", "T"), ("T", "C1"), ("T", "C2"), ("T", "C3"), ("C1", "BF"), ("C2", "BF"),
        ("C3", "BF"), ("BF", "PA"),
        ("PA", "S1"), ("PA", "S2"), ("PA", "S3"), ("PA", "S4"), ("PA", "S5"),
        ("S1", "OJ"), ("S2", "OJ"), ("S2", "TE"), ("S3", "TE"), ("S3", "ES"), ("S4", "ES"), ("S4", "BO"),
        ("S5", "BO"), ("S1", "S2"), ("S2", "S3"), ("S3", "S4"), ("S4", "S5"),
        ("OJ", "LV"), ("TE", "LV"), ("ES", "LV"), ("BO", "LV"), ("LV", "SE"),
        ("SE", "I"), ("SE", "RT"), ("SE", "P2"), ("I", "RT"), ("I", "P1"), ("I", "P2"), ("RT", "P3"), ("RT", "P2"),
        ("P1", "PL"), ("P2", "PL"), ("P2", "E"), ("P3", "E"), ("PL", "ET"), ("E", "ET"), ("ET", "D"), ("PL", "D"))
    c.e(("OJ", "I"), ("BO", "RT"), ("S3", "LV"), ancho=0.95)    # pasillos angostos / atajos de riesgo
    P = [("Abrigo", 1.40, 8, 2.0), ("Traje", 1.60, 8, 2.2), ("Camisa Premium", 0.28, 24, 1.1),
         ("Uniforme Médico", 0.45, 20, 1.0), ("Uniforme Industrial", 0.90, 12, 1.5),
         ("Ropa Deportiva", 0.30, 30, 0.9), ("Ropa Interior", 0.10, 60, 0.6), ("Pijama", 0.35, 24, 0.8),
         ("Chaleco", 0.60, 15, 1.3), ("Delantal", 0.25, 30, 0.7)]
    for p in P:
        c.prenda(*p)
    R = [
        ("Abrigo", "Con termofijado", 60, "A>RC>RV>T>@CORTE>BF>PA>@COSTURA>TE>OJ>LV>SE>I>@PLANCHADO>PL>ET>D"),
        ("Abrigo", "Bordado", 40, "A>RC>RV>T>@CORTE>BF>PA>@COSTURA>BO>TE>LV>SE>I>RT>I>@PLANCHADO>PL>ET>D"),
        ("Traje", "Estándar", 70, "A>RC>RV>T>@CORTE>BF>PA>@COSTURA>TE>OJ>I>@PLANCHADO>PL>ET>D"),
        ("Traje", "Con retrabajo", 30, "A>RC>RV>T>@CORTE>BF>PA>@COSTURA>TE>OJ>I>RT>I>@PLANCHADO>PL>ET>D"),
        ("Camisa Premium", "Lisa", 50, "A>RC>T>@CORTE>BF>PA>@COSTURA>OJ>I>@PLANCHADO>PL>E>D"),
        ("Camisa Premium", "Bordada", 30, "A>RC>T>@CORTE>BF>PA>@COSTURA>BO>OJ>I>@PLANCHADO>PL>E>D"),
        ("Camisa Premium", "Estampada", 20, "A>RC>T>@CORTE>BF>PA>@COSTURA>ES>OJ>I>@PLANCHADO>E>ET>D"),
        ("Uniforme Médico", "Estándar", 80, "A>RC>T>@CORTE>BF>PA>@COSTURA>LV>SE>I>@PLANCHADO>E>ET>D"),
        ("Uniforme Médico", "Bordado", 20, "A>RC>T>@CORTE>BF>PA>@COSTURA>BO>LV>SE>I>@PLANCHADO>E>ET>D"),
        ("Uniforme Industrial", "Lavado industrial", 70, "A>RC>RV>T>@CORTE>BF>PA>@COSTURA>LV>SE>I>E>ET>D"),
        ("Uniforme Industrial", "Estampado", 30, "A>RC>RV>T>@CORTE>BF>PA>@COSTURA>ES>LV>SE>RT>I>E>ET>D"),
        ("Ropa Deportiva", "Estampada", 60, "A>RC>T>@CORTE>BF>PA>@COSTURA>ES>PL>E>D"),
        ("Ropa Deportiva", "Lisa", 40, "A>RC>T>@CORTE>BF>PA>@COSTURA>PL>E>D"),
        ("Ropa Interior", "Única", 100, "A>RC>T>@CORTE>BF>PA>@COSTURA>PL>ET>D"),
        ("Pijama", "Estampada", 50, "A>RC>T>@CORTE>BF>PA>@COSTURA>ES>PL>E>D"),
        ("Pijama", "Lisa", 50, "A>RC>T>@CORTE>BF>PA>@COSTURA>OJ>PL>E>D"),
        ("Chaleco", "Termofijado", 100, "A>RC>RV>T>@CORTE>BF>PA>@COSTURA>TE>OJ>I>@PLANCHADO>E>D"),
        ("Delantal", "Bordado", 40, "A>RC>T>@CORTE>BF>PA>@COSTURA>BO>PL>E>D"),
        ("Delantal", "Liso", 60, "A>RC>T>@CORTE>BF>PA>@COSTURA>PL>E>D"),
    ]
    for r in R:
        c.ruta(*r)
    for p in [("Abrigo", 160, 2, 0, 420), ("Traje", 160, 1, 10, 330), ("Camisa Premium", 480, 3, 20, 470),
              ("Uniforme Médico", 360, 2, 30, 400), ("Uniforme Industrial", 200, 3, 40, 0),
              ("Ropa Deportiva", 600, 4, 50, 0), ("Ropa Interior", 900, 4, 60, 0), ("Pijama", 420, 3, 80, 0),
              ("Chaleco", 150, 2, 100, 380), ("Delantal", 360, 4, 110, 0), ("Traje", 120, 1, 150, 330),
              ("Uniforme Médico", 240, 1, 170, 360), ("Camisa Premium", 300, 2, 190, 450),
              ("Abrigo", 100, 1, 210, 400), ("Ropa Deportiva", 360, 3, 240, 0), ("Uniforme Industrial", 120, 2, 260, 480),
              ("Pijama", 300, 4, 290, 0), ("Chaleco", 100, 1, 320, 440), ("Ropa Interior", 600, 4, 340, 0),
              ("Delantal", 240, 3, 360, 0)]:
        c.pedido(*p)
    return c


if __name__ == "__main__":
    dificil().guardar("03_DIFICIL_camiseria_14_areas.xlsx")
    muy_dificil().guardar("04_MUY_DIFICIL_denim_20_areas.xlsx")
    ultra().guardar("05_ULTRA_planta_3_naves_29_areas.xlsx")
    print("ejemplos generados")
