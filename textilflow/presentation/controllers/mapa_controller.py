from ...domain.entities import Estacion
from ..theme import COLOR_RECURSOS, fmt
from .base import Controlador, construir_animacion, construir_red

COLOR_COLA = "#7E8BA8"


class MapaController(Controlador):
    def __init__(self, vista, ctx, escenarios, layout, procesos, simulacion, rutas):
        super().__init__(vista, ctx)
        self._esc, self._layout, self._procesos = escenarios, layout, procesos
        self._simulacion, self._rutas = simulacion, rutas
        self._resultado = None
        self._anim = None
        self._nodo = None
        self._estaciones: list[Estacion] = []
        v = vista
        v.simular_solicitado.connect(self._simular)
        v.pedido_cambiado.connect(self._consultar)
        v.modo_cambiado.connect(v.mapa.set_modo_calor)
        v.jugar_solicitado.connect(self._alternar)
        v.reiniciar_solicitado.connect(lambda: (v.mapa.pausar(), v.set_jugando(False), v.mapa.set_tiempo(0.0)))
        v.velocidad_cambiada.connect(v.mapa.set_velocidad)
        v.tiempo_solicitado.connect(lambda f: v.mapa.set_tiempo(f * (self._anim.t_fin if self._anim else 0)))
        v.mapa.nodo_clicado.connect(self._nodo_clicado)
        v.mapa.tiempo_cambiado.connect(self._tiempo)
        v.mapa.terminado.connect(lambda: v.set_jugando(False))
        v.mapa.set_velocidad(float(v.combo_vel.currentData()))

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        esc = self._esc.listar(tid) if tid else []
        self.vista.set_escenarios([(e.id, e.nombre) for e in esc])
        nombres = {t.id: t.nombre for t in self._procesos.listar_tipos()}
        peds = self._procesos.listar_pedidos(tid) if tid else []
        self.vista.set_pedidos([(p.id, f"#{p.id} {nombres.get(p.tipo_prenda_id, '?')} · {p.cantidad} u · prio {p.prioridad}")
                                for p in peds])
        self._estaciones = self._layout.listar_estaciones(tid) if tid else []
        if self._resultado is not None and self._resultado.escenario.taller_id != tid:
            self._resultado = self._anim = None
            self.vista.mapa.cargar_animacion(None)
        if self._resultado is None:
            self.vista.mapa.dibujar(*construir_red(self._layout, tid, cerrados=self.ctx.cerrados()))

    def _simular(self, escenario_id: int) -> None:
        if not escenario_id:
            self.vista.error("Cree y seleccione un escenario en «Escenarios y simulación».")
            return
        r = self._intentar(self._simulacion.execute, escenario_id, False)
        if r is None:
            return
        self._resultado = r
        self._anim = construir_animacion(r, self._estaciones)
        m = self.vista.mapa
        m.dibujar(*construir_red(self._layout, self.ctx.taller_id, cerrados=self.ctx.cerrados()))
        m.cargar_animacion(self._anim)
        s = r.series
        self.vista.grafico.set_datos(s["t"], [("En el sistema", "#5CC8FF", s["wip"]), ("Completados", "#6BE3B2", s["completados"]),
                                              ("Esperando", COLOR_COLA, [sum(c[i] for c in s["cola"].values()) for i in range(len(s["t"]))])])
        self._nodo = None
        self.vista.info_nodo.setText("Pulse un área del mapa para ver las rutas que usarán los lotes.")
        self.vista.tabla_rutas.set_filas([])
        self.vista.leyenda_recursos.setText("  ".join(
            f'<span style="color:{COLOR_RECURSOS[i % len(COLOR_RECURSOS)]}">■</span> Recurso {i + 1}'
            for i in range(r.escenario.num_recursos)) + "  · transparente = vacío")
        self._consultar()
        self._tiempo(0.0)
        self.vista.set_jugando(True)
        m.reproducir()
        self.vista.info(f"Animando «{r.escenario.nombre}»: {len(r.proceso.movimientos)} movimientos, "
                        f"{len(r.proceso.lotes)} lotes, cierre en {fmt(r.ind.makespan_min, 0)} min.")

    def _alternar(self) -> None:
        m = self.vista.mapa
        if m.reproduciendo:
            m.pausar()
            self.vista.set_jugando(False)
        elif self._anim:
            m.reproducir()
            self.vista.set_jugando(True)

    def _tiempo(self, t: float) -> None:
        if not self._anim:
            return
        v = self.vista
        v.slider.blockSignals(True)
        v.slider.setValue(int(t / self._anim.t_fin * 1000))
        v.slider.blockSignals(False)
        h, mnt = divmod(int(t), 60)
        v.reloj.setText(f"t = {t:6.1f} min  ({h:02d}:{mnt:02d} h)")
        v.grafico.set_marca(t)
        cola, proc = {}, {}
        for est, lleg, ini, fin in self._anim.visitas:
            if lleg <= t and (ini is None or ini > t):
                cola[est] = cola.get(est, 0) + 1
            elif ini is not None and ini <= t < (fin if fin is not None else 1e18):
                proc[est] = proc.get(est, 0) + 1
        filas = [[f"{e.codigo} · {e.nombre}", cola.get(e.codigo, 0), f"{proc.get(e.codigo, 0)}/{e.capacidad}",
                  fmt(self._anim.utilizacion.get(e.codigo), 0)] for e in self._estaciones if e.tiempo_proceso_min > 0]
        v.tabla_areas.set_filas(filas)
        lotes = self._resultado.proceso.lotes
        hechos = sum(1 for l in lotes if l.fin_min is not None and l.fin_min <= t)
        v.estado_global.setText(f"Lotes completados: {hechos}/{len(lotes)} · esperando: {sum(cola.values())} · "
                                f"en proceso: {sum(proc.values())}")

    def _nodo_clicado(self, codigo: str) -> None:
        if self._resultado is None:
            self.vista.info("Simule y anime un escenario para consultar las rutas de un área.")
            return
        self._nodo = codigo
        self._consultar()

    def _consultar(self) -> None:
        r = self._resultado
        if r is None:
            return
        pedido = self.vista.combo_pedido.currentData()
        almacen = next((e.codigo for e in self._estaciones if e.funcion == "ALMACEN"), None)
        nodo = self._nodo or almacen
        if nodo is None:
            return
        rutas = self._rutas.execute(r, nodo, pedido)
        caminos = [x["camino"] for x in rutas]
        principales = [i for i, x in enumerate(rutas) if x["principal"]]
        orden = sorted(range(len(rutas)), key=lambda i: rutas[i]["principal"])
        self.vista.mapa.resaltar_caminos([caminos[i] for i in orden],
                                         len(orden) - 1 if principales else None, self._nodo)
        alcance = f"del pedido #{pedido}" if pedido else "de todos los pedidos"
        titulo = f"Área {self._nodo}" if self._nodo else "Todas las rutas (desde el Almacén)"
        if rutas:
            tot = sum(x["unidades"] for x in rutas)
            self.vista.info_nodo.setText(f"{titulo}: {len(rutas)} ruta(s) {alcance}, {tot} unidades. "
                                         "Amarillo = principal (más unidades); naranja = alternativas.")
        else:
            self.vista.info_nodo.setText(f"{titulo}: ningún lote {alcance} pasa por aquí en este escenario.")
        self.vista.tabla_rutas.set_filas(
            [[f"#{x['pedido_id']}" + (" ★" if x["principal"] else ""), f"{x['prenda']} · {x['rama']}",
              "→".join(x["camino"]), fmt(x["distancia_m"], 1), x["lotes"], x["unidades"]] for x in rutas])
