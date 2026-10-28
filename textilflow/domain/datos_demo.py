from .entities import Conexion, Estacion, Pedido, Robot, RutaProceso, TipoPrenda

NOMBRE_TALLER = "Confecciones Andina - Caso Experimental 01"

ESTACIONES = [
    ("A", "Almacén", "ALMACEN", 2, 8, 0, 1, ""),
    ("C", "Corte", "PROCESO", 8, 8, 0.6, 3, ""),
    ("CO", "Costura 1", "PROCESO", 14, 6, 2.4, 4, "COSTURA"),
    ("CO2", "Costura 2", "PROCESO", 14, 2, 2.4, 4, "COSTURA"),
    ("B", "Bordado", "PROCESO", 14, 12, 1.05, 1, ""),
    ("I", "Inspección", "PROCESO", 20, 6, 0.4, 2, ""),
    ("P", "Planchado", "PROCESO", 20, 12, 0.7, 2, ""),
    ("E", "Empaque", "PROCESO", 26, 9, 0.5, 2, ""),
    ("D", "Despacho", "DESPACHO", 32, 9, 0, 1, ""),
]

CONEXIONES = [
    ("A", "C", 6.0, 1.8), ("C", "CO", 6.5, 1.8), ("CO", "I", 6.0, 1.8), ("I", "E", 7.0, 1.8),
    ("E", "D", 6.0, 1.8), ("C", "B", 8.0, 1.5), ("CO", "P", 8.5, 0.95), ("I", "P", 6.0, 1.4),
    ("B", "P", 6.5, 1.5), ("P", "E", 7.0, 1.3), ("B", "E", 13.0, 1.5), ("C", "CO2", 9.0, 1.5),
    ("CO", "CO2", 4.0, 1.5), ("CO2", "I", 7.5, 1.5), ("A", "B", 13.0, 1.5), ("A", "P", 19.0, 1.5),
]

PRENDAS = [
    ("Camisa", 0.25, 24, 1.0),
    ("Pantalón", 0.60, 20, 1.2),
    ("Chaqueta", 0.90, 12, 1.8),
    ("Uniforme", 0.50, 20, 1.1),
]

RUTAS = [
    ("Camisa", "Línea normal", 55, "A>C>@COSTURA>I>P>E>D"),
    ("Camisa", "Con bordado", 30, "A>C>B>@COSTURA>I>P>E>D"),
    ("Camisa", "Pieza precortada", 15, "A>@COSTURA>I>E>D"),
    ("Pantalón", "Estándar", 70, "A>C>@COSTURA>P>E>D"),
    ("Pantalón", "Con inspección", 30, "A>C>@COSTURA>I>P>E>D"),
    ("Chaqueta", "Completa", 60, "A>C>@COSTURA>I>P>E>D"),
    ("Chaqueta", "Bordada", 40, "A>C>B>@COSTURA>I>P>E>D"),
    ("Uniforme", "Bordado corporativo", 100, "A>C>B>@COSTURA>P>E>D"),
]

PEDIDOS = [
    ("Camisa", 300, 3, 0, 420),
    ("Pantalón", 200, 2, 15, 340),
    ("Chaqueta", 100, 4, 30, 0),
    ("Uniforme", 150, 1, 60, 330),
    ("Camisa", 250, 3, 100, 470),
]

STOCK = [
    ("Camisa", 400, 50),
    ("Pantalón", 250, 30),
    ("Chaqueta", 120, 20),
    ("Uniforme", 150, 20),
]

ROBOT = ("AMR Andina Experimental 01", 50.0, 0.70, 0.80, 0.90)

ESCENARIOS = [
    ("S0 · Manual (2 operarios)", "MANUAL", 2, 1.0, 25.0, 30.0, 30.0),
    ("S1 · AMR Andina (2 robots)", "AMR", 2, 0.70, 50.0, 30.0, 30.0),
]


def construir(taller_id: int) -> dict:
    return {
        "estaciones": [Estacion(taller_id, c, n, f, x, y, t, cap, g) for c, n, f, x, y, t, cap, g in ESTACIONES],
        "conexiones": [Conexion(taller_id, o, d, dist, w) for o, d, dist, w in CONEXIONES],
        "tipos": [TipoPrenda(n, p, u, f) for n, p, u, f in PRENDAS],
        "robot": Robot(*ROBOT[:5], "DISENO"),
    }
