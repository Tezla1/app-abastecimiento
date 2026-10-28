from ...domain import datos_demo as D
from ...domain.entities import Escenario, Pedido, Robot, RutaProceso, Stock, Taller
from .analisis import EjecutarSimulacion
from .escenarios import GestionarEscenarios
from .layout import GestionarLayout
from .parametros import GestionarParametros
from .procesos import GestionarProcesos
from .robots import GestionarRobots
from .talleres import GestionarTalleres

NOMBRE_DEMO = D.NOMBRE_TALLER


class CargarDatosDemo:
    def __init__(self, talleres: GestionarTalleres, layout: GestionarLayout, procesos: GestionarProcesos,
                 robots: GestionarRobots, escenarios: GestionarEscenarios, simulacion: EjecutarSimulacion,
                 parametros: GestionarParametros, inventario=None):
        self._inv = inventario
        self._t, self._l, self._p, self._r = talleres, layout, procesos, robots
        self._e, self._s, self._par = escenarios, simulacion, parametros

    def execute(self) -> Taller:
        self._par.listar()
        usados = {t.nombre for t in self._t.listar()}
        nombre, n = NOMBRE_DEMO, 1
        # si el ejemplo ya está cargado, se crea otra copia numerada
        while nombre in usados:
            n += 1
            nombre = f"{NOMBRE_DEMO} ({n})"
        taller = self._t.guardar(Taller(nombre, 240.0, 15, 8.0, "SINTETICO",
                                        "Datos sintéticos para validar el software."))
        datos = D.construir(taller.id)
        for e in datos["estaciones"]:
            self._l.guardar_estacion(e)
        for c in datos["conexiones"]:
            self._l.guardar_conexion(c)
        ids = {}
        existentes = {t.nombre.lower(): t for t in self._p.listar_tipos()}
        for tp in datos["tipos"]:
            previo = existentes.get(tp.nombre.lower())
            ids[tp.nombre] = previo.id if previo else self._p.guardar_tipo(tp).id
        for prenda, nombre, frac, seq in D.RUTAS:
            self._p.guardar_ruta(RutaProceso(taller.id, ids[prenda], nombre, frac, seq))
        for prenda, cant, prio, llegada, venc in D.PEDIDOS:
            self._p.guardar_pedido(Pedido(taller.id, ids[prenda], cant, prio, llegada, venc))
        if self._inv is not None:       # el ejemplo trae stock: las camisas no alcanzan para los pedidos
            for prenda, unidades, minimo in D.STOCK:
                self._inv.guardar_stock(Stock(taller.id, ids[prenda], unidades, minimo))
        robot = self._r.guardar(datos["robot"])
        s0, s1 = D.ESCENARIOS
        e0 = self._e.guardar(Escenario(taller.id, s0[0], s0[1], s0[2], 480, s0[3], s0[4], s0[5], s0[6], "A", True))
        e1 = self._e.guardar(Escenario(taller.id, s1[0], s1[1], s1[2], 480, s1[3], s1[4], s1[5], s1[6], "A", True,
                                       robot.id))
        self._s.execute(e0.id)
        self._s.execute(e1.id)
        return taller

    def preparar_escenario_base(self, taller: Taller) -> bool:
        if self._e.listar(taller.id):
            return False
        estaciones = self._l.listar_estaciones(taller.id)
        inicio = next((e.codigo for e in estaciones if e.funcion == "ALMACEN"), None) or (
            estaciones[0].codigo if estaciones else "")
        _, _, _, v, cap, tc, td = D.ESCENARIOS[0]
        # regla sencilla: un operario por cada 5 áreas
        n = max(2, -(-len(estaciones) // 5))
        e0 = self._e.guardar(Escenario(taller.id, f"S0 · Manual ({n} operarios)", "MANUAL", n, 480, v, cap, tc, td,
                                       inicio, True))
        self._s.execute(e0.id)
        return True
